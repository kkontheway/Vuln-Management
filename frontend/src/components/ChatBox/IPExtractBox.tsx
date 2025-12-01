import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import apiService from '@/services/api';

type ApiErrorShape = {
  response?: { data?: { error?: string } };
  message?: string;
};

const getApiErrorMessage = (err: unknown, fallback: string): string => {
  if (typeof err === 'object' && err !== null) {
    const apiError = err as ApiErrorShape;
    return apiError.response?.data?.error ?? apiError.message ?? fallback;
  }
  return fallback;
};

const IPExtractBox = () => {
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [extractedIPs, setExtractedIPs] = useState<string[]>([]);
  const [extractedCVEs, setExtractedCVEs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [csvData, setCsvData] = useState<string | null>(null);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  const handleExtract = async () => {
    if (!inputText.trim()) {
      setError('Please enter some text');
      return;
    }

    setIsLoading(true);
    setError(null);
    setExtractedIPs([]);
    setExtractedCVEs([]);
    setCsvData(null);
    setSaveMessage(null);
    setSaveError(null);
    setShowSaveDialog(false);

    try {
      const response = await apiService.extractIPAddresses(inputText);
      const ips = response.ips || [];
      const cves = response.cves || [];
      setExtractedIPs(ips);
      setExtractedCVEs(cves);
      setCsvData(response.csv || null);
      
      if (ips.length === 0 && cves.length === 0) {
        setError('No indicators found in the text');
      } else {
        setShowSaveDialog(true);
      }
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Failed to extract IP addresses'));
      console.error('Failed to extract IPs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveIndicators = async () => {
    if (isSaving) return;
    setIsSaving(true);
    setSaveMessage(null);
    setSaveError(null);

    try {
      const response = await apiService.saveRecordFutureIndicators({
        ips: extractedIPs,
        cves: extractedCVEs,
        sourceText: inputText,
      });
      setSaveMessage(response.message || 'Indicators saved to RecordFuture');
    } catch (err: unknown) {
      setSaveError(getApiErrorMessage(err, 'Failed to save indicators'));
    } finally {
      setIsSaving(false);
      setShowSaveDialog(false);
    }
  };

  const handleDownloadCSV = () => {
    if (!csvData) return;

    const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `threat_indicators_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    setInputText('');
    setExtractedIPs([]);
    setExtractedCVEs([]);
    setCsvData(null);
    setError(null);
    setSaveMessage(null);
    setSaveError(null);
  };

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle className="text-lg">RecordFuture</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-text-secondary">
            Enter text containing indicators
          </label>
          <Textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste text here... IPs and CVEs will be extracted automatically."
            rows={8}
            className="resize-none"
          />
        </div>

        <div className="flex gap-2">
          <Button
            onClick={() => {
              void handleExtract();
            }}
            disabled={isLoading || !inputText.trim()}
            className="flex-1"
          >
            {isLoading ? 'Extracting...' : 'Extract Indicators'}
          </Button>
          <Button
            variant="outline"
            onClick={handleClear}
            disabled={isLoading}
          >
            Clear
          </Button>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm">
            {error}
          </div>
        )}

        {(extractedIPs.length > 0 || extractedCVEs.length > 0) && (
          <div className="space-y-3">
            {extractedIPs.length > 0 && (
              <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                <div className="text-sm font-medium text-text-primary mb-2">
                  Found {extractedIPs.length} IP address(es):
                </div>
                <div className="flex flex-wrap gap-2">
                  {extractedIPs.map((ip, index) => (
                    <span
                      key={`${ip}-${index}`}
                      className="px-2 py-1 bg-glass-bg border border-glass-border rounded text-sm font-mono"
                    >
                      {ip}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {extractedCVEs.length > 0 && (
              <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                <div className="text-sm font-medium text-text-primary mb-2">
                  Found {extractedCVEs.length} CVE(s):
                </div>
                <div className="flex flex-wrap gap-2">
                  {extractedCVEs.map((cve, index) => (
                    <span
                      key={`${cve}-${index}`}
                      className="px-2 py-1 bg-glass-bg border border-glass-border rounded text-sm font-mono"
                    >
                      {cve}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {csvData && (
              <Button onClick={handleDownloadCSV} className="w-full" variant="default">
                Download CSV File
              </Button>
            )}

            {saveMessage && (
              <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-500 text-sm">
                {saveMessage}
              </div>
            )}

            {saveError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm">
                {saveError}
              </div>
            )}
          </div>
        )}
      </CardContent>

      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save indicators to RecordFuture?</DialogTitle>
            <DialogDescription>
              {`Detected ${extractedIPs.length} IP(s) and ${extractedCVEs.length} CVE(s). Save them to the RecordFuture database?`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowSaveDialog(false)}
              disabled={isSaving}
            >
              Not now
            </Button>
            <Button
              onClick={() => {
                void handleSaveIndicators();
              }}
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Yes, Save'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default IPExtractBox;
