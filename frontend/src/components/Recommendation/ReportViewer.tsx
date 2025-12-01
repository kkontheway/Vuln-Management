import { useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import type { RecommendationReport, CVEVulnerabilityData } from '@/types/api';
import { cn } from '@/lib/utils';

interface ReportViewerProps {
  report: RecommendationReport;
  vulnerabilityData?: CVEVulnerabilityData;
  onClose?: () => void;
  showExportButtons?: boolean;
}

type Html2PdfChain = {
  set: (options: Record<string, unknown>) => Html2PdfChain;
  from: (element: HTMLElement) => Html2PdfChain;
  save: () => Promise<void>;
};

type Html2PdfModule = {
  default: () => Html2PdfChain;
};

const ReportViewer = ({ report, vulnerabilityData, onClose, showExportButtons = true }: ReportViewerProps) => {
  const reportRef = useRef<HTMLDivElement>(null);

  const getSeverityColor = (severity: string | null | undefined) => {
    if (!severity) return 'bg-gray-500';
    const s = severity.toLowerCase();
    if (s.includes('critical')) return 'bg-red-600';
    if (s.includes('high')) return 'bg-orange-500';
    if (s.includes('medium')) return 'bg-yellow-500';
    if (s.includes('low')) return 'bg-green-500';
    return 'bg-gray-500';
  };

  const getSeverityLabel = (severity: string | null | undefined) => {
    if (!severity) return 'UNKNOWN';
    const s = severity.toUpperCase();
    if (s.includes('CRITICAL')) return 'CRITICAL';
    if (s.includes('HIGH')) return 'HIGH';
    if (s.includes('MEDIUM')) return 'MEDIUM';
    if (s.includes('LOW')) return 'LOW';
    return s;
  };

  const exportToPDF = async () => {
    if (!reportRef.current) return;
    
    try {
      // Dynamic import for html2pdf.js to work with Vite
      const html2pdfModule = (await import('html2pdf.js')) as Html2PdfModule;
      const html2pdf = html2pdfModule.default;
      const element = reportRef.current;
      const opt: Record<string, unknown> = {
        margin: 0.5,
        filename: `Vulnerability_Report_${report.cve_id}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
      };
      
      await html2pdf().set(opt).from(element).save();
    } catch (error) {
      console.error('Error exporting to PDF:', error);
      alert('Failed to export PDF. Please try again.');
    }
  };

  const exportToHTML = () => {
    if (!reportRef.current) return;
    
    try {
      const htmlContent = reportRef.current.outerHTML;
      const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vulnerability Report - ${report.cve_id}</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: #F4F7F9;
      margin: 0;
      padding: 20px;
      color: #333;
    }
    .report-container {
      max-width: 1000px;
      margin: 0 auto;
      background: #fff;
      box-shadow: 0 4px 20px rgba(0,0,0,0.08);
      border-radius: 8px;
      overflow: hidden;
    }
  </style>
</head>
<body>
${htmlContent}
</body>
</html>`;
      
      const blob = new Blob([fullHtml], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Vulnerability_Report_${report.cve_id}.html`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting to HTML:', error);
      alert('Failed to export HTML. Please try again.');
    }
  };

  const summary = vulnerabilityData?.summary;
  const software = vulnerabilityData?.software;
  const devices = vulnerabilityData?.affected_devices || [];
  const evidence = vulnerabilityData?.evidence;
  const remediation = vulnerabilityData?.remediation;

  const primaryOsLabel = summary?.os_distribution
    ? Object.entries(summary.os_distribution)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 1)
        .map(([os, count]) => `${os} (${count} hosts)`)
        .join(', ')
    : 'N/A';

  const affectedDepartmentsLabel = summary?.department_distribution
    ? Object.keys(summary.department_distribution).slice(0, 3).join(', ')
    : 'N/A';

  return (
    <div className="w-full">
      {showExportButtons && (
        <div className="mb-4 flex gap-2 justify-end">
          <Button
            variant="outline"
            onClick={() => {
              void exportToPDF();
            }}
          >
            Export PDF
          </Button>
          <Button variant="outline" onClick={exportToHTML}>
            Export HTML
          </Button>
          {onClose && (
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          )}
        </div>
      )}
      
      <div ref={reportRef} className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-900 to-blue-800 text-white p-6 border-b-4 border-yellow-400">
          <div className="flex justify-between items-center flex-wrap gap-4">
            <div>
              <h1 className="text-2xl font-semibold mb-2">
                Batch Vulnerability Report{' '}
                <span className="bg-white/20 px-2 py-1 rounded text-sm font-normal">
                  {report.cve_id}
                </span>
              </h1>
              <div className="text-sm opacity-80">
                Status: {summary?.severity ? getSeverityLabel(summary.severity) : 'Pending Remediation'}
              </div>
            </div>
            <div className="text-center">
              <div className={cn(
                "w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg",
                getSeverityColor(summary?.severity)
              )}>
                {summary?.cvss_score?.toFixed(1) || 'N/A'}
              </div>
              <div className="text-xs mt-1 opacity-90">
                {summary?.severity ? getSeverityLabel(summary.severity) : 'CVSS'}
              </div>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="p-8">
          {/* Impact Scope & Software Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Impact Scope Summary */}
            <div>
              <h2 className="text-base font-bold text-blue-900 border-l-4 border-blue-500 pl-3 mb-4 uppercase tracking-wide">
                Impact Scope Summary
              </h2>
              <Card className="bg-gray-50 p-4 border border-gray-200">
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Total Affected Hosts</span>
                    <span className="font-semibold text-blue-900 text-base">
                      {summary?.total_affected_hosts || 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Primary OS</span>
                    <span className="font-semibold text-blue-900 text-right">
                      {primaryOsLabel}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Affected Departments</span>
                    <span className="font-semibold text-blue-900 text-right">
                      {affectedDepartmentsLabel}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Network Segment</span>
                    <span className="font-semibold text-blue-900 text-right">
                      N/A
                    </span>
                  </div>
                </div>
              </Card>
            </div>

            {/* Vulnerable Software */}
            <div>
              <h2 className="text-base font-bold text-blue-900 border-l-4 border-blue-500 pl-3 mb-4 uppercase tracking-wide">
                Vulnerable Software
              </h2>
              <Card className="bg-gray-50 p-4 border border-gray-200">
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Vendor</span>
                    <span className="font-semibold text-blue-900 text-right">
                      {software?.vendor || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Product</span>
                    <span className="font-semibold text-blue-900 text-right">
                      {software?.name || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Vulnerable Ver</span>
                    <span className="font-semibold text-red-600 text-right">
                      {software?.version || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Detection Type</span>
                    <span className="font-semibold text-blue-900 text-right">
                      Registry & File Ver
                    </span>
                  </div>
                </div>
              </Card>
            </div>
          </div>

          {/* Affected Device List */}
          {devices.length > 0 && (
            <div className="mb-8">
              <h2 className="text-base font-bold text-blue-900 border-l-4 border-blue-500 pl-3 mb-4 uppercase tracking-wide flex justify-between items-center">
                <span>Affected Device List</span>
                <span className="bg-gray-100 text-blue-900 px-2 py-1 rounded text-xs font-semibold">
                  Showing top {Math.min(devices.length, 50)} of {summary?.total_affected_hosts || devices.length}
                </span>
              </h2>
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="overflow-x-auto max-h-[350px] overflow-y-auto">
                  <table className="w-full text-sm min-w-[600px]">
                    <thead className="bg-gray-100 sticky top-0">
                      <tr>
                        <th className="text-left p-3 font-semibold text-blue-900">Hostname</th>
                        <th className="text-left p-3 font-semibold text-blue-900">IP Address</th>
                        <th className="text-left p-3 font-semibold text-blue-900">OS Version</th>
                        <th className="text-left p-3 font-semibold text-blue-900">User</th>
                        <th className="text-left p-3 font-semibold text-blue-900">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {devices.slice(0, 50).map((device, idx) => (
                        <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                          <td className="p-3 font-medium">{device.device_name || device.device_id}</td>
                          <td className="p-3 text-gray-700">N/A</td>
                          <td className="p-3 text-gray-700">
                            {device.os_platform} {device.os_version}
                          </td>
                          <td className="p-3 text-gray-700">{device.rbac_group_name || 'N/A'}</td>
                          <td className="p-3">
                            <span className="flex items-center">
                              <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                              {device.status || 'Vulnerable'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Technical Evidence */}
          {(evidence?.disk_paths?.length || evidence?.registry_paths?.length) && (
            <div className="mb-8">
              <h2 className="text-base font-bold text-blue-900 border-l-4 border-blue-500 pl-3 mb-4 uppercase tracking-wide">
                Common Detection Evidence
              </h2>
              <Card className="bg-gray-800 text-gray-100 p-4 rounded-lg font-mono text-sm">
                <div className="text-gray-400 italic mb-3 text-xs">
                  // Evidence sample from host: {devices[0]?.device_name || 'N/A'}
                </div>
                <div className="space-y-3">
                  {evidence.disk_paths?.slice(0, 5).map((path, idx) => (
                    <div key={idx} className="flex items-start">
                      <span className="text-yellow-400 mr-2">[FILE]</span>
                      <span className="break-all">{path}</span>
                    </div>
                  ))}
                  {evidence.registry_paths?.slice(0, 5).map((path, idx) => (
                    <div key={idx} className="flex items-start">
                      <span className="text-yellow-400 mr-2">[REG]</span>
                      <span className="break-all">{path}</span>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}

          {/* Remediation Plan */}
          <div>
            <h2 className="text-base font-bold text-blue-900 border-l-4 border-blue-500 pl-3 mb-4 uppercase tracking-wide">
              Batch Remediation Plan
            </h2>
            <Card className="bg-yellow-50 border border-yellow-400 p-5 rounded-lg">
              {remediation?.recommended_security_update_id && (
                <h3 className="text-lg font-semibold text-blue-900 mb-3">
                  Deploy Update (ID: {remediation.recommended_security_update_id})
                </h3>
              )}
              <p className="text-gray-700 text-sm leading-relaxed mb-4">
                Since <strong>{summary?.total_affected_hosts || 0} devices</strong> are affected, 
                it is recommended to use a centralized deployment tool (SCCM / Intune / Ansible) 
                rather than manual patching.
              </p>
              {remediation?.recommended_security_update && (
                <ul className="text-sm text-gray-700 space-y-2 mb-4 pl-5 list-disc">
                  <li>
                    <strong>Action:</strong> {remediation.recommended_security_update}
                  </li>
                  {remediation.recommended_security_update_url && (
                    <li>
                      <strong>Update URL:</strong>{' '}
                      <a 
                        href={remediation.recommended_security_update_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        {remediation.recommended_security_update_url}
                      </a>
                    </li>
                  )}
                </ul>
              )}
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportViewer;
