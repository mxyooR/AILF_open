import { apiClient } from '../common/apiClient';
import { 
  Entity, 
  EntityCreateRequest, 
  EntityUpdateRequest,
  EntityRelationship,
  EntityRelationshipCreateRequest,
  EntityDataRecord 
} from '../../types/developer/entity';

// API响应类型定义
interface APIResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

interface EntitiesListResponse {
  entities: Entity[];
  total: number;
}

interface EntityDetailResponse {
  entity: Entity;
}

interface EntityDataResponse {
  records: EntityDataRecord[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

interface RelationshipsResponse {
  relationships: EntityRelationship[];
}

export const entityAPI = {
  // 1. 获取实体列表
  async getEntitiesList(params?: {
    include_fields?: boolean;
    status?: string;
  }): Promise<APIResponse<EntitiesListResponse>> {
    const queryParams = new URLSearchParams();
    if (params?.include_fields !== undefined) queryParams.append('include_fields', params.include_fields.toString());
    if (params?.status) queryParams.append('status', params.status);

    const url = `/api/v1/entities${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await apiClient.get<EntitiesListResponse>(url);
  },

  // 2. 创建实体定义
  async createEntity(entityData: EntityCreateRequest): Promise<APIResponse<EntityDetailResponse>> {
    const url = `/api/v1/entities`;
    return await apiClient.post<EntityDetailResponse>(url, entityData);
  },

  // 3. 获取实体详情
  async getEntityDetail(entityId: string, params?: {
    include_fields?: boolean;
    include_relationships?: boolean;
    include_statistics?: boolean;
  }): Promise<APIResponse<EntityDetailResponse>> {
    const queryParams = new URLSearchParams();
    if (params?.include_fields !== undefined) queryParams.append('include_fields', params.include_fields.toString());
    if (params?.include_relationships !== undefined) queryParams.append('include_relationships', params.include_relationships.toString());
    if (params?.include_statistics !== undefined) queryParams.append('include_statistics', params.include_statistics.toString());

    const url = `/api/v1/entities/${entityId}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await apiClient.get<EntityDetailResponse>(url);
  },

  // 4. 更新实体定义
  async updateEntity(
    entityId: string,
    entityData: EntityUpdateRequest
  ): Promise<APIResponse<EntityDetailResponse>> {
    return await apiClient.put<EntityDetailResponse>(`/api/v1/entities/${entityId}`, entityData);
  },

  // 5. 删除实体定义
  async deleteEntity(entityId: string, params?: {
    force?: boolean;
  }): Promise<APIResponse<{ message: string }>> {
    const queryParams = new URLSearchParams();
    if (params?.force !== undefined) queryParams.append('force', params.force.toString());

    const url = `/api/v1/entities/${entityId}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await apiClient.delete<{ message: string }>(url);
  },

  // 6. 获取实体数据记录列表
  async getEntityData(entityId: string, params?: {
    page?: number;
    page_size?: number;
    limit?: number;
    search?: string;
    sort?: string;
  }): Promise<APIResponse<EntityDataResponse>> {
    const queryParams = new URLSearchParams();
    if (params?.page !== undefined) queryParams.append('page', params.page.toString());
    // 支持 page_size 和 limit 两种参数名，优先使用 limit
    const limitValue = params?.limit ?? params?.page_size;
    if (limitValue !== undefined) queryParams.append('limit', limitValue.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.sort) queryParams.append('sort', params.sort);

    const url = `/api/v1/entities/${entityId}/data${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await apiClient.get<EntityDataResponse>(url);
  },

  // 7. 创建实体数据记录
  async createEntityRecord(
    entityId: string,
    recordData: Record<string, any>
  ): Promise<APIResponse<{ record: EntityDataRecord }>> {
    return await apiClient.post<{ record: EntityDataRecord }>(`/api/v1/entities/${entityId}/data`, recordData);
  },

  // 8. 更新实体数据记录
  async updateEntityRecord(
    entityId: string,
    recordId: string,
    recordData: Record<string, any>
  ): Promise<APIResponse<{ record: EntityDataRecord }>> {
    return await apiClient.put<{ record: EntityDataRecord }>(`/api/v1/entities/${entityId}/data/${recordId}`, recordData);
  },

  // 9. 删除实体数据记录
  async deleteEntityRecord(
    entityId: string,
    recordId: string
  ): Promise<APIResponse<{ message: string }>> {
    return await apiClient.delete<{ message: string }>(`/api/v1/entities/${entityId}/data/${recordId}`);
  },

  // 10. 创建实体关系
  async createRelationship(
    entityId: string,
    relationshipData: EntityRelationshipCreateRequest
  ): Promise<APIResponse<{ relationship: EntityRelationship }>> {
    return await apiClient.post<{ relationship: EntityRelationship }>(`/api/v1/entities/${entityId}/relationships`, relationshipData);
  },

  // 11. 获取实体关系列表
  async getRelationships(entityId: string): Promise<APIResponse<RelationshipsResponse>> {
    return await apiClient.get<RelationshipsResponse>(`/api/v1/entities/${entityId}/relationships`);
  },

  // 12. 删除实体关系
  async deleteRelationship(
    entityId: string,
    relationshipId: string
  ): Promise<APIResponse<{ message: string }>> {
    return await apiClient.delete<{ message: string }>(`/api/v1/entities/${entityId}/relationships/${relationshipId}`);
  },

  // 13. 更新实体关系
  async updateRelationship(
    relationshipId: string,
    relationshipData: EntityRelationshipCreateRequest
  ): Promise<APIResponse<{ relationship: EntityRelationship }>> {
    return await apiClient.put<{ relationship: EntityRelationship }>(`/api/v1/relationships/${relationshipId}`, relationshipData);
  },

  // 14. 获取实体关系详情
  async getRelationshipDetail(
    entityId: string,
    relationshipId: string
  ): Promise<APIResponse<{ relationship: EntityRelationship }>> {
    return await apiClient.get<{ relationship: EntityRelationship }>(`/api/v1/entities/${entityId}/relationships/${relationshipId}`);
  },

  // 额外的辅助方法

  // 批量创建实体
  async batchCreateEntities(entitiesData: EntityCreateRequest[]): Promise<APIResponse<{ entities: Entity[] }>> {
    const promises = entitiesData.map(entityData => this.createEntity(entityData));
    const results = await Promise.allSettled(promises);
    
    const successfulEntities: Entity[] = [];
    const errors: string[] = [];
    
    results.forEach((result, index) => {
      if (result.status === 'fulfilled' && result.value.code === 201) {
        successfulEntities.push(result.value.data.entity);
      } else {
        errors.push(`实体 ${entitiesData[index].displayName} 创建失败`);
      }
    });
    
    return {
      code: errors.length === 0 ? 200 : 207, // 207 Multi-Status
      message: errors.length === 0 ? '批量创建成功' : `部分创建成功，${errors.length} 个失败`,
      data: { entities: successfulEntities }
    };
  },

  // 验证实体名称唯一性
  async validateEntityName(name: string, excludeId?: string): Promise<boolean> {
    try {
      const response = await this.getEntitiesList();
      if (response.code === 200) {
        const existingEntity = response.data.entities.find(entity => 
          entity.name === name && entity.id !== excludeId
        );
        return !existingEntity;
      }
      return true;
    } catch (error) {
      console.error('验证实体名称失败:', error);
      return true; // 验证失败时允许通过
    }
  },

  // 获取实体统计信息
  async getEntityStatistics(entityId: string): Promise<APIResponse<{
    record_count: number;
    field_count: number;
    relationship_count: number;
    last_updated: string;
  }>> {
    const response = await this.getEntityDetail(entityId, {
      include_statistics: true
    });
    
    if (response.code === 200 && response.data.entity.statistics) {
      return {
        code: 200,
        message: '获取统计信息成功',
        data: response.data.entity.statistics
      };
    }
    
    throw new Error('获取统计信息失败');
  },

  // 导出实体配置
  async exportEntityConfig(entityId: string): Promise<APIResponse<{ config: any }>> {
    const response = await this.getEntityDetail(entityId, {
      include_fields: true,
      include_relationships: true
    });
    
    if (response.code === 200) {
      const entity = response.data.entity;
      const config = {
        name: entity.name,
        displayName: entity.displayName,
        description: entity.description,
        icon: entity.icon,
        fields: entity.fields,
        relationships: entity.relationships
      };
      
      return {
        code: 200,
        message: '导出配置成功',
        data: { config }
      };
    }
    
    throw new Error('导出配置失败');
  }
};
