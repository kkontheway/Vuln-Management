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
  vulnerability_severity_level?: string;
  description?: string;
  cvss_score?: number;
  cve_epss?: number;
  cve_public_exploit?: boolean;
  status?: string;
  os_platform?: string;
  software_name?: string;
  software_vendor?: string;
  exploitability_level?: string;
  metasploit_detected?: boolean;
  nuclei_detected?: boolean;
  recordfuture_detected?: boolean;
  affected_devices?: number;
  last_seen_timestamp?: string;
  security_update_available?: boolean;
  recommended_security_update_id?: string;
  recommended_security_update?: string;
  recommended_security_update_url?: string;
  recommendation_reference?: string;
  device_tags?: string[];
}

export interface VulnerabilityDevice {
  device_id?: string;
  device_name?: string;
  rbac_group_name?: string;
  os_platform?: string;
  os_version?: string;
  os_architecture?: string;
  status?: string;
  last_seen_timestamp?: string;
}

export interface VulnerabilityFilters {
  cve_id?: string;
  device_name?: string;
  os_platform?: string;
  os_version?: string;
  software_vendor?: string | string[];
  software_name?: string;
  vulnerability_severity_level?: string;
  status?: string;
  exploitability_level?: string;
  rbac_group_name?: string;
  cvss_min?: string;
  cvss_max?: string;
  epss_min?: string;
  epss_max?: string;
  cve_public_exploit?: string;
  threat_intel?: string | string[];
  date_from?: string;
  date_to?: string;
  device_tag?: string | string[];
}

// Statistics
export interface StatisticsResponse {
  severity: ChartData[];
  platform: ChartData[];
  age_distribution?: AgeDistributionData;
  exploitability_ratio?: ChartData[];
  autopatch_coverage?: AutopatchCoverage;
  autopatch_epss_coverage?: AutopatchEpssCoverage;
  new_vulnerabilities_7days?: number;
  epss_distribution?: ChartData[];
  intel_feed_overlap?: ChartData[];
}

export interface CoverageBreakdown {
  covered: number;
  not_covered: number;
}

export interface AutopatchCoverage {
  critical: CoverageBreakdown;
  high: CoverageBreakdown;
  medium: CoverageBreakdown;
}

export interface AutopatchEpssCoverage {
  low: CoverageBreakdown;
  medium: CoverageBreakdown;
  high: CoverageBreakdown;
  critical: CoverageBreakdown;
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
export type SyncDataSource = string;

export interface SyncSourceDefinition {
  key: string;
  name: string;
  description: string;
  default_enabled: boolean;
  order: number;
}

export interface DataSourceSyncStatus {
  last_sync_time?: string;
  sync_type?: string;
  name?: string;
}

export interface SyncStatus {
  device_vulnerabilities?: DataSourceSyncStatus;
  sources?: Record<string, DataSourceSyncStatus>;
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

export type TrendPeriod = 'week' | 'month' | 'year';

export interface TrendPoint {
  date: string;
  critical: number;
  high: number;
  medium: number;
  carry?: boolean;
}

export type TrendSeries = Record<TrendPeriod, TrendPoint[]>;

export interface DashboardTrendResponse {
  periods: Partial<Record<TrendPeriod, TrendPoint[]>>;
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

export interface PatchThisResponse {
  data: Vulnerability[];
}

export interface VulnerabilityDetailEntry {
  cve_id: string;
  severity?: string;
  description?: string;
  cvss_v3?: number;
  epss?: number;
  cve_public_exploit?: boolean;
  affected_devices?: number;
  last_seen_timestamp?: string;
  devices?: VulnerabilityDevice[];
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
  disk_paths?: string[];
  registry_paths?: string[];
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
  description: string | null;
  total_vulnerabilities: number;
}
export interface SyncProgressSource {
  key: string;
  name: string;
  status: 'pending' | 'running' | 'success' | 'error';
  message?: string;
}
