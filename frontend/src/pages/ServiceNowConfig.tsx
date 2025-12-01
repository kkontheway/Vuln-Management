import { useState, useEffect, useCallback } from 'react';
import type { FormEvent } from 'react';
import apiService from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { getErrorMessage } from '@/utils/error';
import type {
  IntegrationSecretDescriptor,
  IntegrationSettingsResponse,
  IntegrationStatus,
  IntegrationTestResponse,
} from '@/types/integrations';

interface ServiceNowMetadataState {
  instanceUrl: string;
  username: string;
  defaultTable: string;
}

const defaultMetadata: ServiceNowMetadataState = {
  instanceUrl: '',
  username: '',
  defaultTable: 'incident',
};

const ServiceNowConfig = () => {
  const [metadata, setMetadata] = useState<ServiceNowMetadataState>(defaultMetadata);
  const [passwordInput, setPasswordInput] = useState('');
  const [secretStatus, setSecretStatus] = useState<IntegrationSecretDescriptor | null>(null);
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<IntegrationTestResponse | null>(null);

  const getStringMetadata = (value: unknown, fallback: string) =>
    typeof value === 'string' ? value : fallback;

  const syncFromSettings = useCallback((settings: IntegrationSettingsResponse) => {
    const metadataSource = settings.metadata ?? {};
    setMetadata({
      instanceUrl: getStringMetadata(metadataSource.instance_url, ''),
      username: getStringMetadata(metadataSource.username, ''),
      defaultTable: getStringMetadata(metadataSource.default_table, 'incident'),
    });
    setSecretStatus(settings.secrets?.password || null);
    setIntegrationStatus(settings.status || null);
  }, []);

  const loadSettings = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getIntegrationSettings('servicenow');
      syncFromSettings(response);
    } catch (error) {
      console.error('Failed to load ServiceNow settings:', error);
    } finally {
      setIsLoading(false);
    }
  }, [syncFromSettings]);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  const handleChange = (field: keyof ServiceNowMetadataState, value: string) => {
    setMetadata((prev) => ({ ...prev, [field]: value }));
  };

  const buildMetadataPayload = () => ({
    instance_url: metadata.instanceUrl.trim(),
    username: metadata.username.trim(),
    default_table: metadata.defaultTable,
  });

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const settings = await apiService.saveIntegrationSettings({
        provider: 'servicenow',
        metadata: buildMetadataPayload(),
        secrets: passwordInput ? { password: passwordInput } : undefined,
      });
      syncFromSettings(settings);
      setPasswordInput('');
      alert('ServiceNow configuration saved successfully!');
    } catch (error: unknown) {
      alert(getErrorMessage(error, 'Failed to save configuration'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const payload = {
        metadata: buildMetadataPayload(),
        ...(passwordInput ? { secrets: { password: passwordInput } } : {}),
      };
      const result = await apiService.testIntegrationSettings('servicenow', payload);
      setTestResult(result);
      if (result.success) {
        await loadSettings();
      }
    } catch (error: unknown) {
      setTestResult({
        success: false,
        error: getErrorMessage(error, 'Connection test failed'),
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleRotatePassword = async () => {
    if (!passwordInput) {
      alert('Please enter a new password before rotating.');
      return;
    }
    setIsSaving(true);
    try {
      const settings = await apiService.rotateIntegrationSecret('servicenow', {
        secrets: { password: passwordInput },
      });
      syncFromSettings(settings);
      setPasswordInput('');
      alert('Password rotated successfully.');
    } catch (error: unknown) {
      alert(getErrorMessage(error, 'Failed to rotate password'));
    } finally {
      setIsSaving(false);
    }
  };

  const resetConfig = () => {
    setMetadata(defaultMetadata);
    setPasswordInput('');
    setTestResult(null);
  };

  const formatTimestamp = (value?: string | null) => {
    if (!value) return '-';
    try {
      return new Date(value).toLocaleString();
    } catch {
      return value;
    }
  };

  return (
    <div className="space-y-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary mb-2">ServiceNow Configuration</h1>
          <p className="text-text-secondary">
            Credentials are encrypted and stored on the server. Update metadata or rotate passwords from this page.
          </p>
        </div>

        <form
          onSubmit={(event) => {
            void handleSubmit(event);
          }}
          className="space-y-6"
        >
          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>Connection Settings</CardTitle>
              <CardDescription>Configure ServiceNow instance connection</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">ServiceNow Instance URL *</label>
                <Input
                  type="url"
                  value={metadata.instanceUrl}
                  onChange={(e) => handleChange('instanceUrl', e.target.value)}
                  placeholder="https://yourinstance.service-now.com"
                  required
                  disabled={isLoading}
                />
                <p className="text-xs text-text-tertiary">Your ServiceNow instance URL (without trailing slash)</p>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">Username *</label>
                <Input
                  type="text"
                  value={metadata.username}
                  onChange={(e) => handleChange('username', e.target.value)}
                  placeholder="ServiceNow username"
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">Password *</label>
                <Input
                  type="password"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder={secretStatus?.configured ? '•••••••• (stored securely)' : 'ServiceNow password'}
                  disabled={isLoading}
                />
                <p className="text-xs text-text-tertiary">
                  {secretStatus?.configured
                    ? `Password stored securely${secretStatus.last_rotated_at ? ` (rotated ${formatTimestamp(secretStatus.last_rotated_at)})` : ''}`
                    : 'Enter password to configure or rotate'}
                </p>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">Default Table</label>
                <Select value={metadata.defaultTable} onValueChange={(value) => handleChange('defaultTable', value)}>
                  <SelectTrigger disabled={isLoading}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="incident">Incident</SelectItem>
                    <SelectItem value="change_request">Change Request</SelectItem>
                    <SelectItem value="problem">Problem</SelectItem>
                    <SelectItem value="sc_request">Service Catalog Request</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>Health & Testing</CardTitle>
              <CardDescription>Validate stored credentials without exposing secrets</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1 text-sm">
                <div className="text-text-secondary">Last Test Status</div>
                <div className="text-text-primary">
                  {integrationStatus?.last_test_status ? integrationStatus.last_test_status : 'Not tested yet'}
                </div>
                <div className="text-xs text-text-tertiary">
                  {integrationStatus?.last_tested_at ? `Tested at ${formatTimestamp(integrationStatus.last_tested_at)}` : ''}
                </div>
              </div>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  void handleTestConnection();
                }}
                disabled={isTesting || isLoading}
              >
                {isTesting ? 'Testing...' : 'Test Connection'}
              </Button>
              {testResult && (
                <div
                  className={cn(
                    'flex items-center gap-2 p-3 rounded-lg text-sm',
                    testResult.success ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'
                  )}
                >
                  <span>{testResult.success ? '✓' : '✗'}</span>
                  <span>{testResult.message || testResult.error}</span>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex flex-wrap justify-end gap-3">
            <Button type="button" variant="outline" onClick={resetConfig} disabled={isLoading || isSaving}>
              Reset to Defaults
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                void handleRotatePassword();
              }}
              disabled={isSaving || isLoading}
            >
              Rotate Password
            </Button>
            <Button type="submit" disabled={isSaving || isLoading}>
              {isSaving ? 'Saving...' : 'Save Configuration'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ServiceNowConfig;
