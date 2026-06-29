import { useState, useCallback } from 'react';
import { message } from 'antd';
import { entityAPI } from '../../services/developer/entityAPI';
import { 
  Entity, 
  EntityCreateRequest, 
  EntityUpdateRequest,
  EntityRelationship,
  EntityRelationshipCreateRequest 
} from '../../types/developer/entity';

export const useEntityManagement = () => {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);

  // 获取实体列表
  const refreshEntities = useCallback(async () => {
    setLoading(true);
    try {
      const response = await entityAPI.getEntitiesList({
        include_fields: true,
        status: 'active'
      });
      
      if (response.code === 200) {
        setEntities(response.data.entities);
      } else {
        message.error(response.message || '获取实体列表失败');
      }
    } catch (error) {
      console.error('获取实体列表失败:', error);
      message.error('获取实体列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // 创建实体
  const createEntity = useCallback(async (entityData: EntityCreateRequest) => {
    setLoading(true);
    try {
      const response = await entityAPI.createEntity(entityData);
      
      if (response.code === 201) {
        message.success('实体创建成功');
        return response.data.entity;
      } else {
        message.error(response.message || '创建实体失败');
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('创建实体失败:', error);
      message.error('创建实体失败');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // 静默创建实体（用于模板应用，不显示错误消息）
  const createEntitySilently = useCallback(async (entityData: EntityCreateRequest) => {
    try {
      const response = await entityAPI.createEntity(entityData);
      
      if (response.code === 201) {
        return { success: true, entity: response.data.entity };
      } else {
        return { success: false, error: response.message, conflict: response.code === 409 };
      }
    } catch (error: any) {
      // 检查是否是409冲突错误
      const isConflict = error.response?.status === 409 || error.message?.includes('已存在') || error.message?.includes('实体名称已存在');
      return { 
        success: false, 
        error: error.message || '创建实体失败', 
        conflict: isConflict 
      };
    }
  }, []);

  // 获取实体详情
  const getEntityDetail = useCallback(async (entityId: string) => {
    setLoading(true);
    try {
      const response = await entityAPI.getEntityDetail(entityId);
      
      if (response.code === 200) {
        return response.data.entity;
      } else {
        message.error(response.message || '获取实体详情失败');
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('获取实体详情失败:', error);
      message.error('获取实体详情失败');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // 更新实体
  const updateEntity = useCallback(async (entityId: string, entityData: EntityUpdateRequest) => {
    setLoading(true);
    try {
      const response = await entityAPI.updateEntity(entityId, entityData);
      
      if (response.code === 200) {
        message.success('实体更新成功');
        return response.data.entity;
      } else {
        message.error(response.message || '更新实体失败');
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('更新实体失败:', error);
      message.error('更新实体失败');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // 删除实体
  const deleteEntity = useCallback(async (entityId: string, force: boolean = false) => {
    setLoading(true);
    try {
      const response = await entityAPI.deleteEntity(entityId, { force });
      
      if (response.code === 200) {
        message.success('实体删除成功');
        return true;
      } else {
        message.error(response.message || '删除实体失败');
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('删除实体失败:', error);
      message.error('删除实体失败');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // 获取实体数据记录
  const getEntityData = useCallback(async (
    entityId: string, 
    params?: { page?: number; page_size?: number; search?: string; sort?: string }
  ) => {
    setLoading(true);
    try {
      const response = await entityAPI.getEntityData(entityId, params);
      
      if (response.code === 200) {
        return response.data;
      } else {
        message.error(response.message || '获取实体数据失败');
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('获取实体数据失败:', error);
      message.error('获取实体数据失败');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // 创建实体数据记录
  const createEntityRecord = useCallback(async (entityId: string, recordData: Record<string, any>) => {
    setLoading(true);
    try {
      const response = await entityAPI.createEntityRecord(entityId, recordData);
      
      if (response.code === 201) {
        message.success('数据记录创建成功');
        return response.data.record;
      } else {
        message.error(response.message || '创建数据记录失败');
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('创建数据记录失败:', error);
      message.error('创建数据记录失败');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // 更新实体数据记录
  const updateEntityRecord = useCallback(async (
    entityId: string, 
    recordId: string, 
    recordData: Record<string, any>
  ) => {
    setLoading(true);
    try {
      const response = await entityAPI.updateEntityRecord(entityId, recordId, recordData);
      
      if (response.code === 200) {
        message.success('数据记录更新成功');
        return response.data.record;
      } else {
        message.error(response.message || '更新数据记录失败');
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('更新数据记录失败:', error);
      message.error('更新数据记录失败');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // 删除实体数据记录
  const deleteEntityRecord = useCallback(async (entityId: string, recordId: string) => {
    setLoading(true);
    try {
      const response = await entityAPI.deleteEntityRecord(entityId, recordId);
      
      if (response.code === 200) {
        message.success('数据记录删除成功');
        return true;
      } else {
        message.error(response.message || '删除数据记录失败');
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('删除数据记录失败:', error);
      message.error('删除数据记录失败');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // 创建实体关系
  const createRelationship = useCallback(async (
    entityId: string, 
    relationshipData: EntityRelationshipCreateRequest
  ) => {
    setLoading(true);
    try {
      const response = await entityAPI.createRelationship(entityId, relationshipData);
      
      if (response.code === 201) {
        message.success('实体关系创建成功');
        return response.data.relationship;
      } else {
        message.error(response.message || '创建实体关系失败');
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('创建实体关系失败:', error);
      message.error('创建实体关系失败');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // 获取实体关系列表
  const getRelationships = useCallback(async (entityId: string) => {
    setLoading(true);
    try {
      const response = await entityAPI.getRelationships(entityId);
      
      if (response.code === 200) {
        return response.data.relationships;
      } else {
        message.error(response.message || '获取实体关系失败');
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('获取实体关系失败:', error);
      message.error('获取实体关系失败');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // 删除实体关系
  const deleteRelationship = useCallback(async (entityId: string, relationshipId: string) => {
    setLoading(true);
    try {
      const response = await entityAPI.deleteRelationship(entityId, relationshipId);
      
      if (response.code === 200) {
        message.success('实体关系删除成功');
        return true;
      } else {
        message.error(response.message || '删除实体关系失败');
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('删除实体关系失败:', error);
      message.error('删除实体关系失败');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // 更新实体关系
  const updateRelationship = useCallback(async (
    relationshipId: string,
    relationshipData: EntityRelationshipCreateRequest
  ) => {
    setLoading(true);
    try {
      const response = await entityAPI.updateRelationship(relationshipId, relationshipData);
      
      if (response.code === 200) {
        message.success('实体关系更新成功');
        return response.data.relationship;
      } else {
        message.error(response.message || '更新实体关系失败');
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('更新实体关系失败:', error);
      message.error('更新实体关系失败');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    // 状态
    entities,
    loading,
    selectedEntity,
    
    // 实体管理方法
    refreshEntities,
    createEntity,
    createEntitySilently,
    getEntityDetail,
    updateEntity,
    deleteEntity,
    
    // 数据管理方法
    getEntityData,
    createEntityRecord,
    updateEntityRecord,
    deleteEntityRecord,
    
    // 关系管理方法
    createRelationship,
    getRelationships,
    deleteRelationship,
    updateRelationship,
    
    // 状态管理方法
    setSelectedEntity,
  };
};
