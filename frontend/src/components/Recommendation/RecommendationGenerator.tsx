import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
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
import type { RecommendationReport, CVEVulnerabilityData } from '@/types/api';
import ReportViewer from './ReportViewer';

type RecommendationApiError = {
  response?: {
    status?: number;
    data?: {
      error?: string;
      exists?: boolean;
      report?: RecommendationReport;
    };
  };
  message?: string;
};

const isRecommendationApiError = (error: unknown): error is RecommendationApiError =>
  typeof error === 'object' && error !== null;

const getRecommendationErrorMessage = (error: unknown, fallback: string): string => {
  if (isRecommendationApiError(error)) {
    return error.response?.data?.error ?? error.message ?? fallback;
  }
  return fallback;
};

const RecommendationGenerator = () => {
  const navigate = useNavigate();
  const [cveId, setCveId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [existingReport, setExistingReport] = useState<RecommendationReport | null>(null);
  const [showHistoryDialog, setShowHistoryDialog] = useState(false);
  const [reportHistory, setReportHistory] = useState<RecommendationReport[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [selectedReport, setSelectedReport] = useState<RecommendationReport | null>(null);
  const [reportVulnerabilityData, setReportVulnerabilityData] = useState<CVEVulnerabilityData | null>(null);
  const [isLoadingReportData, setIsLoadingReportData] = useState(false);

  const loadReportHistory = useCallback(async () => {
    setIsLoadingHistory(true);
    try {
      const history = await apiService.getRecommendationHistory(50, 0);
      setReportHistory(history.reports);
    } catch (err) {
      console.error('Failed to load report history:', err);
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  // Load report history on component mount
  useEffect(() => {
    void loadReportHistory();
  }, [loadReportHistory]);

  const handleGenerate = async () => {
    if (!cveId.trim()) {
      setError('Please enter a CVE ID');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Check if report exists within 7 days
      const checkResult = await apiService.checkRecommendationReport(cveId.trim());
      
      if (checkResult.exists && checkResult.report) {
        // Show confirmation dialog
        setExistingReport(checkResult.report);
        setShowConfirmDialog(true);
        setIsLoading(false);
        return;
      }

      // No existing report, proceed with generation
      await generateReport(true);
    } catch (err: unknown) {
      setError(getRecommendationErrorMessage(err, 'Failed to check existing report'));
      setIsLoading(false);
    }
  };

  const generateReport = async (force: boolean = false) => {
    setIsLoading(true);
    setError(null);
    setShowConfirmDialog(false);

    try {
      const response = await apiService.generateRecommendationReport({
        cve_id: cveId.trim(),
        force,
      });

      if (response.success) {
        const generatedCveId = cveId.trim();
        setCveId('');
        // Reload report history after successful generation
        await loadReportHistory();
        // Option to view report immediately
        const viewReport = window.confirm(`Report generated successfully! CVE: ${generatedCveId}\n\nWould you like to view the report now?`);
        if (viewReport) {
          navigate(`/report/${generatedCveId}`);
        }
      }
    } catch (err: unknown) {
      if (
        isRecommendationApiError(err) &&
        err.response?.status === 409 &&
        err.response.data?.exists
      ) {
        // Report exists, show confirmation
        setExistingReport(err.response.data.report ?? null);
        setShowConfirmDialog(true);
      } else {
        setError(getRecommendationErrorMessage(err, 'Failed to generate report'));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewHistory = async () => {
    setShowConfirmDialog(false);
    setShowHistoryDialog(true);
    await loadReportHistory();
  };

  const handleViewReport = (report: RecommendationReport) => {
    navigate(`/report/${report.cve_id}`);
  };

  const openReportInDialog = async (report: RecommendationReport) => {
    setSelectedReport(report);
    setShowReportDialog(true);
    setIsLoadingReportData(true);
    try {
      const vulnData = await apiService.getCVEVulnerabilityData(undefined, report.cve_id);
      setReportVulnerabilityData(vulnData);
    } catch (err) {
      console.warn('Failed to load vulnerability data:', err);
    } finally {
      setIsLoadingReportData(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  return (
    <>
      <Card className="glass-panel">
        <CardHeader>
          <CardTitle className="text-lg">Recommendation Report Generator</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              CVE ID
            </label>
            <Input
              value={cveId}
              onChange={(e) => setCveId(e.target.value)}
              placeholder="Enter CVE ID (e.g., CVE-2024-1234)"
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !isLoading) {
                  e.preventDefault();
                  void handleGenerate();
                }
              }}
            />
          </div>

          <Button
            onClick={() => {
              void handleGenerate();
            }}
            disabled={isLoading || !cveId.trim()}
            className="w-full"
          >
            {isLoading ? 'Generating...' : 'Generate Report'}
          </Button>

          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm">
              {error}
            </div>
          )}

          <div className="text-xs text-text-tertiary">
            <p>• Enter a CVE ID to generate a recommendation report</p>
            <p>• If a report was generated within the last 7 days, you'll be prompted to view it or generate a new one</p>
          </div>
        </CardContent>
      </Card>

      {/* Report History List */}
      <Card className="glass-panel mt-6">
        <CardHeader>
          <CardTitle className="text-lg">Report History</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoadingHistory ? (
            <div className="text-center py-8 text-text-secondary">Loading...</div>
          ) : reportHistory.length === 0 ? (
            <div className="text-center py-8 text-text-secondary">No reports found</div>
          ) : (
            <div className="space-y-3">
              {reportHistory.map((report) => (
                <div
                  key={report.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-glass-border bg-glass-bg/50 hover:bg-glass-hover transition-colors"
                >
                  <div className="flex-1">
                    <div className="font-medium text-text-primary">{report.cve_id}</div>
                    <div className="text-xs text-text-secondary mt-1">
                      {formatDate(report.created_at)}
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewReport(report)}
                  >
                    View Report
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Confirmation Dialog for Existing Report */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Report Already Exists</DialogTitle>
            <DialogDescription>
              A report for {cveId} was generated within the last 7 days.
              {existingReport && (
                <span className="block mt-2 text-sm">
                  Created: {formatDate(existingReport.created_at)}
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirmDialog(false)}>
              Cancel
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                void handleViewHistory();
              }}
            >
              View History
            </Button>
            <Button
              onClick={() => {
                void generateReport(true);
              }}
            >
              Continue Generate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* History Dialog */}
      <Dialog open={showHistoryDialog} onOpenChange={setShowHistoryDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Report History</DialogTitle>
            <DialogDescription>
              View all generated recommendation reports
            </DialogDescription>
          </DialogHeader>
          {isLoadingHistory ? (
            <div className="text-center py-8 text-text-secondary">Loading...</div>
          ) : reportHistory.length === 0 ? (
            <div className="text-center py-8 text-text-secondary">No reports found</div>
          ) : (
            <div className="space-y-3">
              {reportHistory.map((report) => (
                <div
                  key={report.id}
                  className="p-4 rounded-lg border border-glass-border bg-glass-bg/50"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium text-text-primary">{report.cve_id}</div>
                    <div className="text-xs text-text-secondary">
                      {formatDate(report.created_at)}
                    </div>
                  </div>
                  {report.report_content && (
                    <div className="text-sm text-text-secondary line-clamp-2">
                      {report.report_content.substring(0, 200)}...
                    </div>
                  )}
                  <div className="flex gap-2 mt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        navigate(`/report/${report.cve_id}`);
                      }}
                    >
                      View Full Page
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        void openReportInDialog(report);
                      }}
                    >
                      View in Dialog
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Report Viewer Dialog */}
      <Dialog open={showReportDialog} onOpenChange={setShowReportDialog}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Vulnerability Report</DialogTitle>
            <DialogDescription>
              Report for {selectedReport?.cve_id}
            </DialogDescription>
          </DialogHeader>
          {selectedReport && (
            <div>
              {isLoadingReportData ? (
                <div className="text-center py-8 text-text-secondary">Loading report data...</div>
              ) : (
                <ReportViewer
                  report={selectedReport}
                  vulnerabilityData={reportVulnerabilityData || undefined}
                  showExportButtons={false}
                  onClose={() => setShowReportDialog(false)}
                />
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default RecommendationGenerator;
