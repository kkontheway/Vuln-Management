import { useState, useEffect, useCallback } from 'react';
import type { FormEvent } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import apiService from '@/services/api';
import { cn } from '@/lib/utils';
import { getErrorMessage } from '@/utils/error';
import type {
  IntegrationSecretDescriptor,
  IntegrationSettingsResponse,
  IntegrationStatus,
  IntegrationTestResponse,
} from '@/types/integrations';

interface ChatMetadataState {
  apiProvider: string;
  baseUrl: string;
  model: string;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
}

const defaultChatMetadata: ChatMetadataState = {
  apiProvider: 'openai',
  baseUrl: 'https://api.openai.com/v1',
  model: 'gpt-3.5-turbo',
  temperature: 0.7,
  maxTokens: 1000,
  systemPrompt: '',
};

const ChatConfig = () => {
  const [metadata, setMetadata] = useState<ChatMetadataState>(defaultChatMetadata);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [secretStatus, setSecretStatus] = useState<IntegrationSecretDescriptor | null>(null);
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<IntegrationTestResponse | null>(null);

  const getStringMetadata = (value: unknown, fallback: string) =>
    typeof value === 'string' ? value : fallback;

  const getNumberMetadata = (value: unknown, fallback: number) =>
    typeof value === 'number' ? value : fallback;

  const syncFromSettings = useCallback((settings: IntegrationSettingsResponse) => {
    const metadataSource = settings.metadata ?? {};
    setMetadata({
      apiProvider: getStringMetadata(metadataSource.api_provider, 'openai'),
      baseUrl: getStringMetadata(metadataSource.base_url, 'https://api.openai.com/v1'),
      model: getStringMetadata(metadataSource.model, 'gpt-3.5-turbo'),
      temperature: getNumberMetadata(metadataSource.temperature, 0.7),
      maxTokens: getNumberMetadata(metadataSource.max_tokens, 1000),
      systemPrompt: getStringMetadata(metadataSource.system_prompt, ''),
    });
    setSecretStatus(settings.secrets?.api_key || null);
    setIntegrationStatus(settings.status || null);
  }, []);

  const loadSettings = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getIntegrationSettings('ai');
      syncFromSettings(response);
    } catch (error) {
      console.error('Failed to load AI config:', error);
    } finally {
      setIsLoading(false);
    }
  }, [syncFromSettings]);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  const handleChange = (field: keyof ChatMetadataState, value: string | number) => {
    setMetadata((prev) => ({ ...prev, [field]: value }));
  };

  const buildMetadataPayload = () => ({
    api_provider: metadata.apiProvider,
    base_url: metadata.baseUrl,
    model: metadata.model,
    temperature: metadata.temperature,
    max_tokens: metadata.maxTokens,
    system_prompt: metadata.systemPrompt,
  });

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const settings = await apiService.saveIntegrationSettings({
        provider: 'ai',
        metadata: buildMetadataPayload(),
        secrets: apiKeyInput ? { api_key: apiKeyInput } : undefined,
      });
      syncFromSettings(settings);
      setApiKeyInput('');
      alert('AI configuration saved successfully!');
    } catch (error: unknown) {
      alert(getErrorMessage(error, 'Failed to save configuration'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const payload = {
        metadata: buildMetadataPayload(),
        ...(apiKeyInput ? { secrets: { api_key: apiKeyInput } } : {}),
      };
      const result = await apiService.testIntegrationSettings('ai', payload);
      setTestResult(result);
      if (result.success) {
        await loadSettings();
      }
    } catch (error: unknown) {
      setTestResult({
        success: false,
        error: getErrorMessage(error, 'AI connection test failed'),
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleRotateKey = async () => {
    if (!apiKeyInput) {
      alert('Please enter a new API key before rotating.');
      return;
    }
    setIsSaving(true);
    try {
      const settings = await apiService.rotateIntegrationSecret('ai', {
        secrets: { api_key: apiKeyInput },
      });
      syncFromSettings(settings);
      setApiKeyInput('');
      alert('API key rotated successfully.');
    } catch (error: unknown) {
      alert(getErrorMessage(error, 'Failed to rotate API key'));
    } finally {
      setIsSaving(false);
    }
  };

  const resetConfig = () => {
    setMetadata(defaultChatMetadata);
    setApiKeyInput('');
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
          <h1 className="text-2xl font-semibold text-text-primary mb-2">AI Chat Configuration</h1>
          <p className="text-text-secondary">Manage AI provider credentials centrally.</p>
        </div>

        <form
          onSubmit={(event) => {
            void handleSubmit(event);
          }}
          className="space-y-6"
        >
          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>API Provider Settings</CardTitle>
              <CardDescription>Configure your AI service provider</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">API Provider</label>
                <Select value={metadata.apiProvider} onValueChange={(value) => handleChange('apiProvider', value)}>
                  <SelectTrigger disabled={isLoading}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="deepseek">DeepSeek</SelectItem>
                    <SelectItem value="anthropic">Anthropic (Claude)</SelectItem>
                    <SelectItem value="custom">Custom API</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">API Key</label>
                <Input
                  type="password"
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  placeholder={secretStatus?.configured ? '•••••••• (stored securely)' : 'Enter your API key'}
                  disabled={isLoading}
                />
                <p className="text-xs text-text-tertiary">
                  {secretStatus?.configured
                    ? `API key stored${secretStatus.last_rotated_at ? ` (rotated ${formatTimestamp(secretStatus.last_rotated_at)})` : ''}`
                    : 'API key will be encrypted on the server'}
                </p>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">Base URL</label>
                <Input
                  type="text"
                  value={metadata.baseUrl}
                  onChange={(e) => handleChange('baseUrl', e.target.value)}
                  placeholder="https://api.openai.com/v1"
                  disabled={isLoading}
                />
              </div>
            </CardContent>
          </Card>

          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>Model Settings</CardTitle>
              <CardDescription>Configure AI model parameters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">Model</label>
                <Select value={metadata.model} onValueChange={(value) => handleChange('model', value)}>
                  <SelectTrigger disabled={isLoading}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                    <SelectItem value="gpt-4">GPT-4</SelectItem>
                    <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                    <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                    <SelectItem value="deepseek-chat">DeepSeek Chat</SelectItem>
                    <SelectItem value="deepseek-reasoner">DeepSeek Reasoner</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">Temperature</label>
                <Input
                  type="number"
                  value={metadata.temperature}
                  onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
                  min="0"
                  max="2"
                  step="0.1"
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-text-secondary">Max Tokens</label>
                <Input
                  type="number"
                  value={metadata.maxTokens}
                  onChange={(e) => handleChange('maxTokens', parseInt(e.target.value) || 0)}
                  min="1"
                  max="4000"
                  disabled={isLoading}
                />
              </div>
            </CardContent>
          </Card>

          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>System Prompt</CardTitle>
              <CardDescription>Define the AI's role and behavior</CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                value={metadata.systemPrompt}
                onChange={(e) => handleChange('systemPrompt', e.target.value)}
                placeholder="Enter system prompt..."
                rows={6}
                disabled={isLoading}
              />
            </CardContent>
          </Card>

          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>Health & Testing</CardTitle>
              <CardDescription>Use stored credentials to verify connectivity</CardDescription>
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
                  void handleTest();
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
            <Button type="button" variant="outline" onClick={resetConfig} disabled={isSaving || isLoading}>
              Reset to Defaults
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                void handleRotateKey();
              }}
              disabled={isSaving || isLoading}
            >
              Rotate API Key
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

export default ChatConfig;
