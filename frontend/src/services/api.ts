import axios, { AxiosInstance } from 'axios';
import type {
  Vulnerability,
  VulnerabilityFilters,
  StatisticsResponse,
  SeverityCounts,
  UniqueCveCount,
  SyncStatus,
  SyncResponse,
  Snapshot,
  SnapshotDetails,
  SnapshotsTrendResponse,
  DashboardTrendResponse,
  ChatRequest,
  ChatResponse,
  FixedVulnerability,
  VulnerabilityDetailEntry,
  SyncSourceDefinition,
  SyncProgressSource,
  PatchThisResponse,
  TrendSeries,
  TrendPeriod,
} from '@/types/api';
import type {
  ServiceNowTicketCreate,
  ServiceNowTicketResponse,
  ServiceNowTicketsResponse,
  ServiceNowNote,
  ServiceNowNotesResponse,
  ServiceNowNoteAdd,
} from '@/types/servicenow';
import type {
  IntegrationSettingsResponse,
  IntegrationSettingsSaveRequest,
  IntegrationSettingsTestRequest,
  IntegrationTestResponse,
} from '@/types/integrations';
import type {
  RecommendationCheckResponse,
  RecommendationGenerateRequest,
  RecommendationGenerateResponse,
  RecommendationHistoryResponse,
  RecommendationReport,
  CVEVulnerabilityData,
  RecordFutureExtractionResponse,
  RecordFutureSaveResponse,
} from '@/types/api';

type QueryParams = Record<string, string | number | boolean | undefined>;

interface VulnerabilitiesResponse {
  data: Vulnerability[];
  total: number;
  page?: number;
  per_page?: number;
  total_pages?: number;
}

interface FixedVulnerabilitiesResponse {
  data: FixedVulnerability[];
}

interface SyncProgressResponse {
  stage: string;
  progress: number;
  message: string;
  is_complete: boolean;
  is_syncing: boolean;
  sources?: SyncProgressSource[];
}

interface SyncSourcesResponse {
  sources: SyncSourceDefinition[];
}

interface CreateSnapshotResponse {
  snapshot_id?: number;
  error?: string;
}

interface SnapshotsResponse {
  snapshots: Snapshot[];
}

interface RecommendationReportResponse {
  report: RecommendationReport;
}

const API_BASE_URL = '/api';

// Create axios instance with default config
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  paramsSerializer: (params: Record<string, string | number | boolean | string[] | number[] | undefined | null>) => {
    const searchParams = new URLSearchParams();
    Object.keys(params).forEach((key) => {
      const value = params[key];
      if (Array.isArray(value)) {
        // For arrays, add each value with the same key (aligns with FastAPI query parsing)
        value.forEach((item) => {
          searchParams.append(key, String(item));
        });
      } else if (value !== null && value !== undefined && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    return searchParams.toString();
  },
});

// API Service Functions
export const apiService = {
  // Vulnerabilities
  getVulnerabilities: async (params: VulnerabilityFilters = {}): Promise<VulnerabilitiesResponse> => {
    const response = await api.get<VulnerabilitiesResponse>('/vulnerabilities', { params });
    return response.data;
  },

  // Statistics
  getStatistics: async (): Promise<StatisticsResponse> => {
    const response = await api.get<StatisticsResponse>('/statistics');
    return response.data;
  },

  getUniqueCveCount: async (): Promise<UniqueCveCount> => {
    const response = await api.get<UniqueCveCount>('/unique-cve-count');
    return response.data;
  },

  getSeverityCounts: async (): Promise<SeverityCounts> => {
    const response = await api.get<SeverityCounts>('/severity-counts');
    return response.data;
  },

  // Filter Options
  getFilterOptions: async (): Promise<Record<string, string[]>> => {
    const response = await api.get<Record<string, string[]>>('/filter-options');
    return response.data;
  },

  getFixedVulnerabilities: async (limit: number = 50): Promise<FixedVulnerabilitiesResponse> => {
    const response = await api.get<FixedVulnerabilitiesResponse>('/fixed-vulnerabilities', { params: { limit } });
    return response.data;
  },

  getPatchThisVulnerabilities: async (options?: { limit?: number; vendorScope?: string }): Promise<PatchThisResponse> => {
    const params: Record<string, string | number> = {};
    if (options?.limit !== undefined) {
      params.limit = options.limit;
    }
    if (options?.vendorScope) {
      params.vendor_scope = options.vendorScope;
    }
    const response = await api.get<PatchThisResponse>('/patch-this', { params: Object.keys(params).length ? params : undefined });
    return response.data;
  },

  getVulnerabilityCatalogEntry: async (cveId: string): Promise<VulnerabilityDetailEntry> => {
    const response = await api.get<VulnerabilityDetailEntry>(`/vulnerability-catalog/${encodeURIComponent(cveId)}`);
    return response.data;
  },

  // Sync
  getSyncStatus: async (): Promise<SyncStatus> => {
    const response = await api.get<SyncStatus>('/sync-status');
    return response.data;
  },

  getSyncSources: async (): Promise<SyncSourceDefinition[]> => {
    const response = await api.get<SyncSourcesResponse>('/sync-sources');
    return response.data.sources;
  },

  getSyncProgress: async (): Promise<SyncProgressResponse> => {
    const response = await api.get<SyncProgressResponse>('/sync-progress');
    return response.data;
  },

  triggerSync: async (dataSources: string[] = []): Promise<SyncResponse> => {
    const response = await api.post<SyncResponse>('/sync', { data_sources: dataSources });
    return response.data;
  },

  // Snapshots
  createInitialSnapshot: async (): Promise<CreateSnapshotResponse> => {
    const response = await api.post<CreateSnapshotResponse>('/create-initial-snapshot');
    return response.data;
  },

  getSnapshots: async (): Promise<SnapshotsResponse> => {
    const response = await api.get<SnapshotsResponse>('/snapshots');
    return response.data;
  },

  getSnapshotDetails: async (snapshotId: number): Promise<SnapshotDetails> => {
    const response = await api.get<SnapshotDetails>(`/snapshots/${snapshotId}/details`);
    return response.data;
  },

  getSnapshotsTrend: async (): Promise<SnapshotsTrendResponse> => {
    const response = await api.get<SnapshotsTrendResponse>('/snapshots/trend');
    return response.data;
  },

  getDashboardTrends: async (period?: TrendPeriod): Promise<TrendSeries> => {
    const params = period ? { period } : undefined;
    const response = await api.get<DashboardTrendResponse>('/dashboard/trends', { params });
    const payload = response.data?.periods ?? {};
    return {
      week: payload.week ?? [],
      month: payload.month ?? [],
      year: payload.year ?? [],
    } satisfies TrendSeries;
  },

  getCveHistory: async (cveId: string): Promise<Record<string, unknown>> => {
    const response = await api.get<Record<string, unknown>>(`/cve-history/${cveId}`);
    return response.data;
  },

  // Chat
  sendChatMessage: async (message: string, config?: ChatRequest['config']): Promise<ChatResponse> => {
    const payload: ChatRequest = { message, ...(config ? { config } : {}) };
    const response = await api.post<ChatResponse>('/chat', payload);
    return response.data;
  },

  // ServiceNow
  getServiceNowTickets: async (params: QueryParams = {}): Promise<ServiceNowTicketsResponse> => {
    const response = await api.get<ServiceNowTicketsResponse>('/servicenow/tickets', { params });
    return response.data;
  },

  getServiceNowTicket: async (ticketId: string): Promise<ServiceNowTicketResponse> => {
    const response = await api.get<ServiceNowTicketResponse>(`/servicenow/tickets/${ticketId}`);
    return response.data;
  },

  createServiceNowTicket: async (ticketData: ServiceNowTicketCreate): Promise<ServiceNowTicketResponse> => {
    const response = await api.post<ServiceNowTicketResponse>('/servicenow/tickets', ticketData);
    return response.data;
  },

  getServiceNowTicketNotes: async (ticketId: string): Promise<ServiceNowNotesResponse> => {
    const response = await api.get<ServiceNowNotesResponse>(`/servicenow/tickets/${ticketId}/notes`);
    return response.data;
  },

  addServiceNowTicketNote: async (ticketId: string, noteText: string): Promise<{ note: ServiceNowNote; message: string }> => {
    const response = await api.post<{ note: ServiceNowNote; message: string }>(
      `/servicenow/tickets/${ticketId}/notes`,
      { note: noteText } as ServiceNowNoteAdd,
    );
    return response.data;
  },

  // Integrations
  getIntegrationSettings: async (provider: string): Promise<IntegrationSettingsResponse> => {
    const response = await api.get<IntegrationSettingsResponse>('/integrations/settings', { params: { provider } });
    return response.data;
  },

  saveIntegrationSettings: async (payload: IntegrationSettingsSaveRequest): Promise<IntegrationSettingsResponse> => {
    const response = await api.post<{ settings: IntegrationSettingsResponse }>('/integrations/settings', payload);
    return response.data.settings;
  },

  testIntegrationSettings: async (provider: string, payload?: IntegrationSettingsTestRequest): Promise<IntegrationTestResponse> => {
    const response = await api.post<IntegrationTestResponse>(`/integrations/settings/${provider}/test`, payload);
    return response.data;
  },

  rotateIntegrationSecret: async (provider: string, payload: IntegrationSettingsTestRequest): Promise<IntegrationSettingsResponse> => {
    const response = await api.post<{ settings: IntegrationSettingsResponse }>(
      `/integrations/settings/${provider}/rotate`,
      payload,
    );
    return response.data.settings;
  },

  // Threat Intelligence
  extractIPAddresses: async (text: string): Promise<RecordFutureExtractionResponse> => {
    const response = await api.post<RecordFutureExtractionResponse>('/threat-intelligence/extract-ip', { text });
    return response.data;
  },

  saveRecordFutureIndicators: async (payload: {
    ips: string[];
    cves: string[];
    sourceText: string;
  }): Promise<RecordFutureSaveResponse> => {
    const response = await api.post<RecordFutureSaveResponse>('/threat-intelligence/recordfuture/save', payload);
    return response.data;
  },

  // Recommendations
  checkRecommendationReport: async (cveId: string): Promise<RecommendationCheckResponse> => {
    const response = await api.get<RecommendationCheckResponse>(`/recommendations/check/${cveId}`);
    return response.data;
  },

  generateRecommendationReport: async (request: RecommendationGenerateRequest): Promise<RecommendationGenerateResponse> => {
    const response = await api.post<RecommendationGenerateResponse>('/recommendations/generate', request);
    return response.data;
  },

  getRecommendationHistory: async (limit: number = 50, offset: number = 0): Promise<RecommendationHistoryResponse> => {
    const response = await api.get<RecommendationHistoryResponse>('/recommendations/history', { params: { limit, offset } });
    return response.data;
  },

  getRecommendationReport: async (reportId: number): Promise<RecommendationReportResponse> => {
    const response = await api.get<RecommendationReportResponse>(`/recommendations/${reportId}`);
    return response.data;
  },

  getRecommendationReportByCVE: async (cveId: string): Promise<RecommendationReportResponse> => {
    const response = await api.get<RecommendationReportResponse>(`/recommendations/cve/${cveId}`);
    return response.data;
  },

  getCVEVulnerabilityData: async (reportId?: number, cveId?: string): Promise<CVEVulnerabilityData> => {
    let url = '';
    if (reportId) {
      url = `/recommendations/${reportId}/vulnerabilities`;
    } else if (cveId) {
      url = `/recommendations/cve/${cveId}/vulnerabilities`;
    } else {
      throw new Error('Either reportId or cveId is required');
    }
    const response = await api.get<CVEVulnerabilityData>(url);
    return response.data;
  },
};

export default apiService;
