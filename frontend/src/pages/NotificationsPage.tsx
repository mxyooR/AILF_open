import React, { useCallback, useEffect, useMemo, useState } from 'react';
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

  const loadNotifications = useCallback(
    async (targetPage: number) => {
      if (!authState.isAuthenticated) return;
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<NotificationListData>('/api/v1/notifications', {
          params: {
            page: targetPage,
            limit: PAGE_SIZE
          }
        });
        const data = response.data || {};
        const records = Array.isArray(data.items) ? data.items : [];
        const totalCount = typeof data.total === 'number' ? data.total : records.length;
        const unread =
          typeof data.unread_count === 'number'
            ? data.unread_count
            : records.filter((item) => !isRead(item)).length;
        setItems(records);
        setTotal(totalCount);
        setUnreadCount(unread);
        setPage(typeof data.page === 'number' && data.page > 0 ? data.page : targetPage);
        setHasNext(Boolean(data.has_next));
        setHasPrev(Boolean(data.has_prev));
      } catch (loadError) {
        const message = loadError instanceof Error ? loadError.message : '查询通知失败';
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [authState.isAuthenticated, isRead]
  );

  useEffect(() => {
    loadNotifications(page);
  }, [loadNotifications, page]);

  const handleMarkRead = useCallback(
    async (item: NotificationItem) => {
      const id = getNotificationId(item);
      if (!id || isRead(item)) return;
      setMarkingId(id);
      try {
        await apiClient.post(`/api/v1/notifications/${encodeURIComponent(id)}/read`);
        setItems((prev) =>
          prev.map((record) => {
            if (getNotificationId(record) !== id) return record;
            return {
              ...record,
              status: '已读',
              is_read: true,
              read: true,
              read_time: new Date().toISOString()
            };
          })
        );
        setUnreadCount((prev) => (prev > 0 ? prev - 1 : 0));
      } catch (markError) {
        const message = markError instanceof Error ? markError.message : '标记已读失败';
        setError(message);
      } finally {
        setMarkingId(null);
      }
    },
    [getNotificationId, isRead]
  );

  const handleDelete = useCallback(
    async (item: NotificationItem) => {
      const id = getNotificationId(item);
      if (!id) return;
      setDeletingId(id);
      setError(null);
      try {
        await apiClient.delete(`/api/v1/notifications/${encodeURIComponent(id)}`);
        const deletedUnread = !isRead(item);
        setItems((prev) => prev.filter((record) => getNotificationId(record) !== id));
        setTotal((prev) => Math.max(0, prev - 1));
        if (deletedUnread) {
          setUnreadCount((prev) => (prev > 0 ? prev - 1 : 0));
        }
      } catch (deleteError) {
        const message = deleteError instanceof Error ? deleteError.message : '删除通知失败';
        setError(message);
      } finally {
        setDeletingId(null);
      }
    },
    [getNotificationId, isRead]
  );

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
            <button className="primary-btn" onClick={() => loadNotifications(page)} disabled={loading}>
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
                      <span>发送时间：{formatDateTime(item.sent_at || item.created_at)}</span>
                      {item.read_time && <span>已读时间：{formatDateTime(item.read_time)}</span>}
                    </div>
                  </div>
                  <div className="notification-actions">
                    {!read && getNotificationId(item) && (
                      <button
                        className="mark-read-btn"
                        onClick={() => handleMarkRead(item)}
                        disabled={markingId === getNotificationId(item) || deletingId === getNotificationId(item)}
                      >
                        {markingId === getNotificationId(item) ? '处理中...' : '标记已读'}
                      </button>
                    )}
                    {getNotificationId(item) && (
                      <button
                        className="delete-btn"
                        onClick={() => handleDelete(item)}
                        disabled={deletingId === getNotificationId(item) || markingId === getNotificationId(item)}
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
            <button className="ghost-btn" onClick={() => setPage((prev) => Math.max(1, prev - 1))} disabled={!hasPrev || loading}>
              上一页
            </button>
            <button className="ghost-btn" onClick={() => setPage((prev) => prev + 1)} disabled={!hasNext || loading}>
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationsPage;
