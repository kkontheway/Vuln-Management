// API Response Types

export interface ApiResponse<T = unknown> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page?: number;
  pageSize?: number;
}

// Vulnerabilities
export interface Vulnerability {
  id: string | number;
  cve_id: string;
  severity?: string;
  platform?: string;
  device_name?: string;
  device_id?: string;
  first_seen?: string;
  last_seen?: string;
  status?: string;
  description?: string;
  cvss_score?: number;
  // Additional fields that might come from API
  vulnerability_severity_level?: string;
  os_platform?: string;
  os_version?: string;
  os_architecture?: string;
  software_vendor?: string;
  software_name?: string;
  software_version?: string;
  exploitability_level?: string;
  first_seen_timestamp?: string;
  last_seen_timestamp?: string;
  autopatch_covered?: boolean;
  metasploit_detected?: boolean;
  nuclei_detected?: boolean;
  recordfuture_detected?: boolean;
  // Device and RBAC fields
  rbac_group_name?: string;
  // Security update fields
  security_update_available?: boolean;
  recommended_security_update?: string;
  recommended_security_update_id?: string;
  recommended_security_update_url?: string;
  recommendation_reference?: string;
  // Path fields (JSON)
  disk_paths?: string[] | Record<string, unknown>;
  registry_paths?: string[] | Record<string, unknown>;
  // Timestamp fields
  event_timestamp?: string;
  last_synced?: string;
  last_updated?: string;
  catalog_description?: string;
  catalog_epss?: number;
}

export interface VulnerabilityFilters {
  severity?: string;
  platform?: string;
  cve_id?: string;
  device_name?: string;
  status?: string;
  exploitability?: string;
  cvss_min?: string;
  cvss_max?: string;
  os_platform?: string;
  exploitability_level?: string;
  software_vendor?: string | string[]; // Support both single value and array for multi-select
  threat_intel?: string | string[];
}

// Statistics
export interface StatisticsResponse {
  severity: ChartData[];
  platform: ChartData[];
  age_distribution?: AgeDistributionData;
  exploitability_ratio?: ChartData[];
  autopatch_coverage?: AutopatchCoverage;
  new_vulnerabilities_7days?: number;
  epss_distribution?: ChartData[];
  intel_feed_overlap?: ChartData[];
}

export interface AutopatchCoverage {
  critical: { covered: number; not_covered: number };
  high: { covered: number; not_covered: number };
  medium: { covered: number; not_covered: number };
}

export interface ChartData {
  name: string;
  value: number;
}

export interface AgeDistributionData {
  [ageRange: string]: {
    Critical?: number;
    High?: number;
    Medium?: number;
    Low?: number;
    Other?: number;
  };
}

export interface SeverityCounts {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface UniqueCveCount {
  unique_cve_count: number;
}

// Sync
export type SyncDataSource = 'device_vulnerabilities' | 'vulnerability_list';

export interface DataSourceSyncStatus {
  last_sync_time?: string;
  sync_type?: string;
}

export interface SyncStatus {
  device_vulnerabilities?: DataSourceSyncStatus;
  vulnerability_list?: DataSourceSyncStatus;
  is_syncing?: boolean;
}

export interface SyncResponse {
  message: string;
  sync_id?: string;
  data_sources?: SyncDataSource[];
}

// Snapshots
export interface Snapshot {
  snapshot_id: number;
  snapshot_time: string;
  total_vulnerabilities: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
}

export interface SnapshotDetails {
  snapshot: Snapshot;
  cve_count: number;
  device_count: number;
}

export interface SnapshotTrend {
  date: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface SnapshotsTrendResponse {
  trend: SnapshotTrend[];
}

// Chat
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  config?: {
    apiKey: string;
    baseUrl: string;
    model: string;
    temperature?: number;
    maxTokens?: number;
    systemPrompt?: string;
  };
}

export interface ChatResponse {
  response: string;
  error?: string;
}

// Filter Options
export interface FilterOptions {
  severities: string[];
  platforms: string[];
  statuses: string[];
  cve_ids: string[];
  device_names: string[];
  // Backend returns these fields directly
  vulnerability_severity_level?: string[];
  os_platform?: string[];
  status?: string[];
  exploitability_level?: string[];
  rbac_group_name?: string[];
}

// Fixed Vulnerabilities
export interface FixedVulnerability {
  cve_id: string;
  device_name?: string;
  severity?: string;
  fixed_date?: string;
}

export interface FixedVulnerabilitiesResponse {
  data: FixedVulnerability[];
}

export interface VulnerabilityCatalogEntry {
  cve_id: string;
  name?: string;
  description?: string;
  severity?: string;
  cvss_v3?: number;
  cvss_vector?: string;
  exposed_machines?: number;
  public_exploit?: boolean;
  exploit_verified?: boolean;
  exploit_in_kit?: boolean;
  epss?: number;
  published_on?: string;
  updated_on?: string;
}

// Recommendation Reports
export interface RecommendationReport {
  id: number;
  cve_id: string;
  report_content?: string;
  ai_prompt?: string;
  created_at: string;
  updated_at: string;
}

export interface RecommendationCheckResponse {
  exists: boolean;
  report?: RecommendationReport;
}

export interface RecommendationGenerateRequest {
  cve_id: string;
  config?: ChatRequest['config'];
  force?: boolean;
}

export interface RecommendationGenerateResponse {
  success: boolean;
  report_id: number;
  cve_id: string;
  message: string;
}

export interface RecommendationHistoryResponse {
  reports: RecommendationReport[];
  total: number;
}

// RecordFuture
export interface RecordFutureExtractionResponse {
  ips: string[];
  cves?: string[];
  csv?: string | null;
  count?: number;
  message?: string;
}

export interface RecordFutureSaveResponse {
  processed: number;
  saved: number;
  message?: string;
}

// CVE Vulnerability Data for Reports
export interface AffectedDevice {
  device_id: string;
  device_name: string;
  os_platform: string;
  os_version: string;
  rbac_group_name: string;
  status: string;
}

export interface ImpactScopeSummary {
  total_affected_hosts: number;
  os_distribution: Record<string, number>;
  department_distribution: Record<string, number>;
  cvss_score: number | null;
  severity: string | null;
}

export interface SoftwareInfo {
  vendor: string;
  name: string;
  version: string;
}

export interface Evidence {
  disk_paths: string[];
  registry_paths: string[];
}

export interface RemediationInfo {
  security_update_available: boolean;
  recommended_security_update: string;
  recommended_security_update_id: string;
  recommended_security_update_url: string;
  recommendation_reference: string;
}

export interface CVEVulnerabilityData {
  cve_id: string;
  summary: ImpactScopeSummary;
  software: SoftwareInfo;
  affected_devices: AffectedDevice[];
  evidence: Evidence;
  remediation: RemediationInfo;
  total_vulnerabilities: number;
}
