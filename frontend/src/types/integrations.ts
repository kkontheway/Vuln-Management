export interface IntegrationSecretDescriptor {
  configured: boolean;
  last_rotated_at?: string | null;
  version?: number | null;
}

export interface IntegrationStatus {
  last_test_status?: string | null;
  last_tested_at?: string | null;
  last_test_message?: string | null;
}

export interface IntegrationSettingsResponse {
  provider: string;
  metadata: Record<string, unknown>;
  secrets: Record<string, IntegrationSecretDescriptor>;
  status: IntegrationStatus;
}

export interface IntegrationSettingsSaveRequest {
  provider: string;
  metadata?: Record<string, unknown>;
  secrets?: Record<string, unknown>;
}

export interface IntegrationSettingsTestRequest {
  metadata?: Record<string, unknown>;
  secrets?: Record<string, unknown>;
}

export interface IntegrationTestResponse {
  success: boolean;
  message?: string;
  error?: string;
}
