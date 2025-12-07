import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import type { Vulnerability } from '@/types/api';
import { formatDate } from '@/utils/formatters';
import VulnerabilityDetailDialog from '@/components/Table/components/VulnerabilityDetailDialog';
import { renderSeverityBadge } from '@/components/Table/components/severityBadge';

interface PatchThisTableProps {
  data: Vulnerability[];
  title?: string;
}

const PatchThisTable = ({ data, title = 'PatchThis' }: PatchThisTableProps) => {
  const [selectedVuln, setSelectedVuln] = useState<Vulnerability | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  const handleViewDetails = (vuln: Vulnerability) => {
    setSelectedVuln(vuln);
    setShowDetailModal(true);
  };

  const renderThreatIntelBadges = (vuln: Vulnerability) => {
    const badges: React.ReactNode[] = [];
    if (vuln.metasploit_detected) {
      badges.push(
        <span key="metasploit" className="px-2 py-1 text-xs rounded-full bg-red-500/10 text-red-500 border border-red-500/30">
          Metasploit
        </span>
      );
    }
    if (vuln.nuclei_detected) {
      badges.push(
        <span key="nuclei" className="px-2 py-1 text-xs rounded-full bg-purple-500/10 text-purple-500 border border-purple-500/30">
          Nuclei
        </span>
      );
    }
    if (vuln.recordfuture_detected) {
      badges.push(
        <span key="recordfuture" className="px-2 py-1 text-xs rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/30">
          RecordFuture
        </span>
      );
    }
    if (badges.length === 0) {
      return <span className="text-text-tertiary text-sm">-</span>;
    }
    return <div className="flex gap-2 flex-wrap">{badges}</div>;
  };

  const renderKevBadge = (value: boolean | undefined) => {
    if (typeof value !== 'boolean') {
      return <span className="text-text-tertiary text-sm">-</span>;
    }
    const baseClass = 'px-2 py-1 text-xs rounded-full border';
    if (value) {
      return (
        <span className={`${baseClass} bg-red-500/10 text-red-500 border-red-500/30`}>
          True
        </span>
      );
    }
    return (
      <span className={`${baseClass} bg-blue-500/10 text-blue-500 border-blue-500/30`}>
        False
      </span>
    );
  };

  const renderReasonTags = (vuln: Vulnerability) => {
    const tags: React.ReactNode[] = [];
    if (typeof vuln.cve_epss === 'number' && vuln.cve_epss > 0.9) {
      tags.push(
        <span key="epss" className="px-2 py-0.5 text-xs rounded-full bg-orange-500/10 text-orange-500 border border-orange-500/30">
          EPSS &gt; 0.9
        </span>
      );
    }
    if (vuln.exploitability_level && /active/i.test(vuln.exploitability_level)) {
      tags.push(
        <span key="active" className="px-2 py-0.5 text-xs rounded-full bg-rose-500/10 text-rose-500 border border-rose-500/30">
          Active Exploit
        </span>
      );
    }
    if (vuln.recordfuture_detected) {
      tags.push(
        <span key="rf" className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/30">
          RecordFuture
        </span>
      );
    }
    if (tags.length === 0) {
      return <span className="text-text-tertiary text-sm">-</span>;
    }
    return <div className="flex gap-2 flex-wrap">{tags}</div>;
  };

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <div className="flex h-[200px] items-center justify-center text-text-tertiary">
            No urgent vulnerabilities found
          </div>
        ) : (
          <div className="overflow-x-auto">
            <div className="max-h-[400px] overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>CVE ID</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>EPSS</TableHead>
                    <TableHead>KEV</TableHead>
                    <TableHead>Signals</TableHead>
                    <TableHead>Reasons</TableHead>
                    <TableHead>Last Seen</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.map((item) => (
                    <TableRow key={item.cve_id}>
                      <TableCell className="font-semibold text-text-primary">
                        {item.cve_id}
                      </TableCell>
                      <TableCell>{renderSeverityBadge(item.severity)}</TableCell>
                      <TableCell>{typeof item.cve_epss === 'number' ? item.cve_epss.toFixed(3) : '-'}</TableCell>
                      <TableCell>{renderKevBadge(item.cve_public_exploit)}</TableCell>
                      <TableCell>{renderThreatIntelBadges(item)}</TableCell>
                      <TableCell>{renderReasonTags(item)}</TableCell>
                      <TableCell>{formatDate(item.last_seen_timestamp)}</TableCell>
                      <TableCell>
                        <Button variant="outline" size="sm" onClick={() => handleViewDetails(item)}>
                          Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}
      </CardContent>

      <VulnerabilityDetailDialog
        open={showDetailModal}
        onOpenChange={setShowDetailModal}
        vulnerability={selectedVuln}
      />
    </Card>
  );
};

export default PatchThisTable;
