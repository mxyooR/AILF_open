export interface ServicePackageInfo {
  name: string;
  display_name: string;
  origin: 'builtin' | 'plugin';
  version?: string | null;
  description?: string | null;
  package_path?: string | null;
  methods: string[];
}

export interface ServicePackageListResponse {
  services: ServicePackageInfo[];
}
