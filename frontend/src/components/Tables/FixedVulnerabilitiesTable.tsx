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
import type { FixedVulnerability, Vulnerability } from '@/types/api';
import { formatDate } from '@/utils/formatters';
import VulnerabilityDetailDialog from '@/components/Table/components/VulnerabilityDetailDialog';

interface FixedVulnerabilitiesTableProps {
  data: FixedVulnerability[];
  limit?: number;
}

const FixedVulnerabilitiesTable = ({ data, limit = 15 }: FixedVulnerabilitiesTableProps) => {
  const displayData = data.slice(0, limit);
  const [selectedVuln, setSelectedVuln] = useState<Vulnerability | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  const handleViewDetails = (item: FixedVulnerability) => {
    const mapped: Vulnerability = {
      id: `${item.cve_id || 'unknown'}-${item.device_name || 'device'}`,
      cve_id: item.cve_id,
      device_name: item.device_name,
      severity: item.severity,
      status: 'Fixed',
      last_seen: item.fixed_date,
      last_seen_timestamp: item.fixed_date,
      first_seen: item.fixed_date,
      first_seen_timestamp: item.fixed_date,
    } as Vulnerability;
    setSelectedVuln(mapped);
    setShowDetailModal(true);
  };

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle className="text-lg">Recently Fixed Vulnerabilities</CardTitle>
      </CardHeader>
      <CardContent>
        {displayData.length === 0 ? (
          <div className="flex h-[200px] items-center justify-center text-text-tertiary">
            No fixed vulnerabilities found
          </div>
        ) : (
          <div className="max-h-[400px] overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[150px]">CVE ID</TableHead>
                  <TableHead className="w-[180px]">Fixed Date</TableHead>
                  <TableHead className="w-[120px]">Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {displayData.map((item, index) => (
                  <TableRow key={`${item.cve_id}-${item.device_name}-${index}`}>
                    <TableCell className="font-medium text-sm">
                      {item.cve_id || '-'}
                    </TableCell>
                    <TableCell className="text-sm text-text-secondary">
                      {item.fixed_date ? formatDate(item.fixed_date) : '-'}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewDetails(item)}
                      >
                        Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
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

export default FixedVulnerabilitiesTable;
