import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/common/apiClient';
import { useUserAuth } from '../hooks/user/useUserAuth';
import '../styles/notifications-page.css';

interface NotificationItem {
  id?: string | number;
  notification_id?: string;
  title?: string;
  message?: string;
  content?: string;
  status?: string;
  is_read?: boolean;
  read?: boolean;
  sent_at?: string;
  send_time?: string;
  created_at?: string;
  read_time?: string;
}

interface NotificationListData {
  items?: NotificationItem[];
  total?: number;
  page?: number;
  limit?: number;
  has_next?: boolean;
  has_prev?: boolean;
  unread_count?: number;
}

const PAGE_SIZE = 20;

const NotificationsPage: React.FC = () => {
  const navigate = useNavigate();
  const { authState } = useUserAuth();
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [markingId, setMarkingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const requestVersion = useRef(0);
  const actionPending = useRef(false);
  const identity = authState.isAuthenticated ? authState.user?.id : null;
  const identityRef = useRef(identity);
  identityRef.current = identity;

  useEffect(() => {
    document.body.className = 'notifications-page-body';
    document.body.style.animation = 'none';
    document.body.style.background = '#f4f7fb';
    document.body.style.backgroundImage = 'none';
    return () => {
      document.body.className = '';
      document.body.style.animation = '';
      document.body.style.background = '';
      document.body.style.backgroundImage = '';
    };
  }, []);

  const getNotificationId = useCallback((item: NotificationItem): string => {
    const raw = item.notification_id ?? item.id;
    return raw == null ? '' : String(raw);
  }, []);

  const isRead = useCallback((item: NotificationItem): boolean => {
    const status = String(item.status || '').toLowerCase();
    return item.is_read === true || item.read === true || status === 'read' || status === '已读';
  }, []);

  const formatDateTime = useCallback((value?: string): string => {
    if (!value) return '未记录';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString('zh-CN', { hour12: false });
  }, []);

  const loadNotifications = useCallback(async (targetPage: number) => {
    if (identity == null) return;
    const version = ++requestVersion.current;
    const current = () => version === requestVersion.current && identity === identityRef.current;
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<NotificationListData>('/api/v1/notifications', {
        params: { page: targetPage, limit: PAGE_SIZE }
      });
      if (!current()) return;
      const data = response.data || {};
      const records = Array.isArray(data.items) ? data.items : [];
      const totalCount = typeof data.total === 'number' ? data.total : records.length;
      setItems(records);
      setTotal(totalCount);
      setUnreadCount(typeof data.unread_count === 'number' ? data.unread_count : records.filter(item => !isRead(item)).length);
      setHasNext(data.has_next ?? targetPage * PAGE_SIZE < totalCount);
      setHasPrev(data.has_prev ?? targetPage > 1);
    } catch (error) {
      if (current()) setError(error instanceof Error ? error.message : '查询通知失败');
    } finally {
      if (current()) setLoading(false);
    }
  }, [identity, isRead]);

  useEffect(() => {
    // 账号变化时取消旧响应并回到第一页，避免显示上个账号的通知。
    requestVersion.current += 1;
    setItems([]);
    setTotal(0);
    setUnreadCount(0);
    setPage(1);
    setHasNext(false);
    setHasPrev(false);
    setLoading(false);
    setError(null);
    actionPending.current = false;
    setMarkingId(null);
    setDeletingId(null);
  }, [identity]);

  useEffect(() => {
    void loadNotifications(page);
    return () => { requestVersion.current += 1; };
  }, [loadNotifications, page]);

  const mutateNotification = useCallback(async (item: NotificationItem, action: 'read' | 'delete') => {
    const id = getNotificationId(item);
    if (!id || identity == null || actionPending.current || (action === 'read' && isRead(item))) return;
    actionPending.current = true;
    requestVersion.current += 1;
    setError(null);
    if (action === 'read') setMarkingId(id);
    else setDeletingId(id);
    try {
      const endpoint = `/api/v1/notifications/${encodeURIComponent(id)}`;
      if (action === 'read') await apiClient.post(`${endpoint}/read`);
      else await apiClient.delete(endpoint);
      if (identityRef.current !== identity) return;
      // 删除最后一项时退回上一页，并从服务端重算数量和分页状态。
      const targetPage = action === 'delete' && items.length === 1 ? Math.max(1, page - 1) : page;
      if (targetPage !== page) setPage(targetPage);
      else await loadNotifications(targetPage);
    } catch (error) {
      if (identityRef.current === identity) setError(error instanceof Error ? error.message : '通知操作失败');
    } finally {
      if (identityRef.current === identity) {
        actionPending.current = false;
        setMarkingId(null);
        setDeletingId(null);
      }
    }
  }, [getNotificationId, identity, isRead, items.length, page, loadNotifications]);

  const handleMarkRead = (item: NotificationItem) => mutateNotification(item, 'read');
  const handleDelete = (item: NotificationItem) => mutateNotification(item, 'delete');

  const totalPages = useMemo(() => {
    if (total <= 0) return 1;
    return Math.max(1, Math.ceil(total / PAGE_SIZE));
  }, [total]);

  if (!authState.isAuthenticated) {
    return (
      <div className="notifications-page">
        <div className="notifications-card empty">
          <h2>请先登录</h2>
          <p>登录后才能查看通知列表。</p>
          <button className="primary-btn" onClick={() => navigate('/')}>
            返回主页
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="notifications-page">
      <div className="notifications-card">
        <div className="notifications-header">
          <div>
            <h1>通知中心</h1>
            <p>
              未读 {unreadCount} 条 · 共 {total} 条
            </p>
          </div>
          <div className="notifications-actions">
            <button className="ghost-btn" onClick={() => navigate('/')}>
              返回主页
            </button>
            <button className="primary-btn" onClick={() => loadNotifications(page)} disabled={loading || !!markingId || !!deletingId}>
              {loading ? '刷新中...' : '刷新'}
            </button>
          </div>
        </div>

        {error && <div className="notifications-error">{error}</div>}

        {loading ? (
          <div className="notifications-loading">正在加载通知...</div>
        ) : items.length === 0 ? (
          <div className="notifications-empty">暂无通知</div>
        ) : (
          <div className="notifications-list">
            {items.map((item) => {
              const id = getNotificationId(item) || `${item.title || ''}-${item.sent_at || ''}`;
              const read = isRead(item);
              return (
                <div className={`notification-item ${read ? 'read' : 'unread'}`} key={id}>
                  <div className="notification-main">
                    <div className="notification-title-row">
                      <h3>{item.title || '系统通知'}</h3>
                      <span className={`notification-status ${read ? 'read' : 'unread'}`}>
                        {read ? '已读' : '未读'}
                      </span>
                    </div>
                    <p>{item.message || item.content || '暂无内容'}</p>
                    <div className="notification-meta">
                      <span>发送时间：{formatDateTime(item.sent_at || item.send_time || item.created_at)}</span>
                      {item.read_time && <span>已读时间：{formatDateTime(item.read_time)}</span>}
                    </div>
                  </div>
                  <div className="notification-actions">
                    {!read && getNotificationId(item) && (
                      <button
                        className="mark-read-btn"
                        onClick={() => handleMarkRead(item)}
                        disabled={!!markingId || !!deletingId || loading}
                      >
                        {markingId === getNotificationId(item) ? '处理中...' : '标记已读'}
                      </button>
                    )}
                    {getNotificationId(item) && (
                      <button
                        className="delete-btn"
                        onClick={() => handleDelete(item)}
                        disabled={!!markingId || !!deletingId || loading}
                      >
                        {deletingId === getNotificationId(item) ? '删除中...' : '删除'}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="notifications-footer">
          <span>
            第 {page} / {totalPages} 页
          </span>
          <div className="pagination-actions">
            <button className="ghost-btn" onClick={() => setPage((prev) => Math.max(1, prev - 1))} disabled={!hasPrev || loading || !!markingId || !!deletingId}>
              上一页
            </button>
            <button className="ghost-btn" onClick={() => setPage((prev) => prev + 1)} disabled={!hasNext || loading || !!markingId || !!deletingId}>
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationsPage;
