import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReportViewer from '@/components/Recommendation/ReportViewer';
import apiService from '@/services/api';
import type { RecommendationReport, CVEVulnerabilityData } from '@/types/api';
import { Button } from '@/components/ui/button';
import { getErrorMessage } from '@/utils/error';

const ReportView = () => {
  const { cveId } = useParams<{ cveId: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<RecommendationReport | null>(null);
  const [vulnerabilityData, setVulnerabilityData] = useState<CVEVulnerabilityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadReport = async () => {
      if (!cveId) {
        setError('CVE ID is required');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Load report by CVE ID
        const reportResponse = await apiService.getRecommendationReportByCVE(cveId);
        setReport(reportResponse.report);

        // Load vulnerability data
        try {
          const vulnData = await apiService.getCVEVulnerabilityData(undefined, cveId);
          setVulnerabilityData(vulnData);
        } catch (vulnError: unknown) {
          console.warn('Failed to load vulnerability data:', vulnError);
          // Continue without vulnerability data
        }
      } catch (err: unknown) {
        setError(getErrorMessage(err, 'Failed to load report'));
      } finally {
        setLoading(false);
      }
    };

    void loadReport();
  }, [cveId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64 rounded-2xl border border-border/40 bg-pop/40">
          <div className="text-text-secondary">Loading report...</div>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col items-center justify-center h-64 space-y-4 rounded-2xl border border-border/40 bg-pop/40">
          <div className="text-destructive">{error || 'Report not found'}</div>
          <Button variant="outline" onClick={() => navigate('/tools')}>
            Back to Tools
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary mb-2">Vulnerability Report</h1>
          <p className="text-text-secondary">Report for {report.cve_id}</p>
        </div>
        <Button variant="outline" onClick={() => navigate('/tools')}>
          Back to Tools
        </Button>
      </div>
      
      <div className="max-w-6xl">
        <ReportViewer 
          report={report} 
          vulnerabilityData={vulnerabilityData || undefined}
          showExportButtons={true}
        />
      </div>
    </div>
  );
};

export default ReportView;
