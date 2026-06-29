import { apiClient } from '../common/apiClient';
import type { APIResponse } from '../common/apiClient';
import type { ServicePackageListResponse } from '../../types/developer/servicePackage';

export const servicePackageAPI = {
  async listPackages(): Promise<APIResponse<ServicePackageListResponse>> {
    return await apiClient.get('/api/v1/service-packages');
  },

  async uploadPackage(file: File, autoRegister: boolean = true): Promise<APIResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);
    const query = autoRegister ? '?auto_register=true' : '';
    const response = await fetch(`/api/v1/service-packages/upload${query}`, {
      method: 'POST',
      body: formData,
      headers: (apiClient.getDeveloperToken() || apiClient.getUserToken())
        ? { Authorization: `Bearer ${apiClient.getDeveloperToken() || apiClient.getUserToken()}` }
        : undefined
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data?.message || 'Upload failed');
    }
    return data;
  }
};

export default servicePackageAPI;
