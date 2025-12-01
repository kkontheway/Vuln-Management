import { useState, useEffect, useMemo, useCallback } from 'react';
import { mockThreats } from '@/data/mockThreats';
import { formatDate } from '@/utils/formatters';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { ThreatIntelligence, ThreatFilters } from '@/types/threat';
import { cn } from '@/lib/utils';

interface ThreatTableProps {
  filters: ThreatFilters;
}

const ThreatTable = ({ filters }: ThreatTableProps) => {
  const [threats, setThreats] = useState<ThreatIntelligence[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    perPage: 50,
    totalPages: 1,
    total: 0,
  });
  const [selectedThreat, setSelectedThreat] = useState<ThreatIntelligence | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  // Filter threats based on filters
  const filteredThreats = useMemo(() => {
    let result = [...mockThreats];

    if (filters.threatType) {
      result = result.filter(t => t.threatType === filters.threatType);
    }
    if (filters.severity) {
      result = result.filter(t => t.severity === filters.severity);
    }
    if (filters.source) {
      result = result.filter(t => t.source === filters.source);
    }
    if (filters.cveId) {
      result = result.filter(t => 
        t.cveIds?.some(cve => cve.toLowerCase().includes(filters.cveId!.toLowerCase()))
      );
    }
    if (filters.iocType) {
      result = result.filter(t => 
        t.iocs.some(ioc => ioc.type === filters.iocType)
      );
    }
    if (filters.iocValue) {
      const searchValue = filters.iocValue.toLowerCase();
      result = result.filter(t => 
        t.iocs.some(ioc => ioc.value.toLowerCase().includes(searchValue))
      );
    }
    if (filters.attacker) {
      const searchValue = filters.attacker.toLowerCase();
      result = result.filter(t => 
        t.attackerInfo?.name?.toLowerCase().includes(searchValue) ||
        t.attackerInfo?.group?.toLowerCase().includes(searchValue) ||
        t.attackerInfo?.country?.toLowerCase().includes(searchValue)
      );
    }
    if (filters.dateFrom) {
      result = result.filter(t => t.timestamp >= filters.dateFrom!);
    }
    if (filters.dateTo) {
      result = result.filter(t => t.timestamp <= filters.dateTo!);
    }

    return result;
  }, [filters]);

  const loadThreats = useCallback(() => {
    try {
      setLoading(true);
      const start = (pagination.page - 1) * pagination.perPage;
      const end = start + pagination.perPage;
      const paginatedThreats = filteredThreats.slice(start, end);
      
      setThreats(paginatedThreats);
      setPagination((prev) => ({
        ...prev,
        totalPages: Math.ceil(filteredThreats.length / prev.perPage),
        total: filteredThreats.length,
      }));
    } catch (error) {
      console.error('Failed to load threats:', error);
    } finally {
      setLoading(false);
    }
  }, [filteredThreats, pagination.page, pagination.perPage]);

  useEffect(() => {
    loadThreats();
  }, [loadThreats]);

  const handlePageChange = (newPage: number) => {
    setPagination((prev) => ({ ...prev, page: newPage }));
  };

  const handlePerPageChange = (value: string) => {
    setPagination((prev) => ({ ...prev, perPage: parseInt(value), page: 1 }));
  };

  const handleShowDetail = (threat: ThreatIntelligence) => {
    setSelectedThreat(threat);
    setShowDetailModal(true);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'Critical':
        return 'text-red-500 bg-red-500/10';
      case 'High':
        return 'text-orange-500 bg-orange-500/10';
      case 'Medium':
        return 'text-yellow-500 bg-yellow-500/10';
      case 'Low':
        return 'text-blue-500 bg-blue-500/10';
      default:
        return 'text-gray-500 bg-gray-500/10';
    }
  };

  const getIOCIcon = (type: string) => {
    switch (type) {
      case 'IP':
        return '🌐';
      case 'Domain':
        return '🔗';
      case 'FileHash':
        return '📄';
      default:
        return '📌';
    }
  };

  return (
    <>
      <Card className="glass-panel">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Threat Intelligence</CardTitle>
            <div className="flex items-center gap-2">
              <span className="text-sm text-text-secondary">Per page:</span>
              <Select
                value={pagination.perPage.toString()}
                onValueChange={handlePerPageChange}
              >
                <SelectTrigger className="w-20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="25">25</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                  <SelectItem value="200">200</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-text-secondary">Loading...</div>
          ) : threats.length === 0 ? (
            <div className="text-center py-8 text-text-secondary">No threats found</div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Threat Type</TableHead>
                      <TableHead>Severity</TableHead>
                      <TableHead>CVE IDs</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {threats.map((threat) => (
                      <TableRow key={threat.id}>
                        <TableCell className="font-medium">{threat.threatType}</TableCell>
                        <TableCell>
                          <span
                            className={cn(
                              'px-2 py-1 rounded text-xs font-medium',
                              getSeverityColor(threat.severity)
                            )}
                          >
                            {threat.severity}
                          </span>
                        </TableCell>
                        <TableCell>
                          {threat.cveIds && threat.cveIds.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {threat.cveIds.slice(0, 2).map((cve) => (
                                <span
                                  key={cve}
                                  className="text-xs px-1.5 py-0.5 bg-blue-500/10 text-blue-500 rounded"
                                >
                                  {cve}
                                </span>
                              ))}
                              {threat.cveIds.length > 2 && (
                                <span className="text-xs text-text-secondary">
                                  +{threat.cveIds.length - 2}
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-text-secondary text-sm">-</span>
                          )}
                        </TableCell>
                        <TableCell>{threat.source}</TableCell>
                        <TableCell>{formatDate(threat.timestamp)}</TableCell>
                        <TableCell>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleShowDetail(threat)}
                          >
                            View Details
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-text-secondary">
                  Showing {((pagination.page - 1) * pagination.perPage) + 1} to{' '}
                  {Math.min(pagination.page * pagination.perPage, pagination.total)} of{' '}
                  {pagination.total} threats
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(pagination.page - 1)}
                    disabled={pagination.page === 1}
                  >
                    Previous
                  </Button>
                  <span className="flex items-center px-3 text-sm text-text-secondary">
                    Page {pagination.page} of {pagination.totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(pagination.page + 1)}
                    disabled={pagination.page >= pagination.totalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Threat Intelligence Details</DialogTitle>
            <DialogDescription>
              Complete information about the threat
            </DialogDescription>
          </DialogHeader>
          {selectedThreat && (
            <div className="space-y-4">
              {/* Basic Information */}
              <div>
                <h3 className="font-semibold text-text-primary mb-2">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-text-secondary">Threat Type:</span>
                    <span className="ml-2 text-text-primary">{selectedThreat.threatType}</span>
                  </div>
                  <div>
                    <span className="text-text-secondary">Severity:</span>
                    <span
                      className={cn(
                        'ml-2 px-2 py-1 rounded text-xs font-medium',
                        getSeverityColor(selectedThreat.severity)
                      )}
                    >
                      {selectedThreat.severity}
                    </span>
                  </div>
                  <div>
                    <span className="text-text-secondary">Source:</span>
                    <span className="ml-2 text-text-primary">{selectedThreat.source}</span>
                  </div>
                  <div>
                    <span className="text-text-secondary">Timestamp:</span>
                    <span className="ml-2 text-text-primary">
                      {formatDate(selectedThreat.timestamp)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Description */}
              <div>
                <h3 className="font-semibold text-text-primary mb-2">Description</h3>
                <p className="text-sm text-text-secondary">{selectedThreat.description}</p>
              </div>

              {/* CVE IDs */}
              {selectedThreat.cveIds && selectedThreat.cveIds.length > 0 && (
                <div>
                  <h3 className="font-semibold text-text-primary mb-2">CVE Associations</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedThreat.cveIds.map((cve) => (
                      <a
                        key={cve}
                        href={`https://cve.mitre.org/cgi-bin/cvename.cgi?name=${cve}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm px-2 py-1 bg-blue-500/10 text-blue-500 rounded hover:bg-blue-500/20"
                      >
                        {cve}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* IOCs */}
              {selectedThreat.iocs && selectedThreat.iocs.length > 0 && (
                <div>
                  <h3 className="font-semibold text-text-primary mb-2">Indicators of Compromise (IOCs)</h3>
                  <div className="space-y-2">
                    {selectedThreat.iocs.map((ioc, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-2 p-2 bg-glass-bg rounded border border-glass-border"
                      >
                        <span className="text-lg">{getIOCIcon(ioc.type)}</span>
                        <span className="text-sm font-medium text-text-secondary">{ioc.type}:</span>
                        <span className="text-sm text-text-primary font-mono">{ioc.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Attacker Information */}
              {selectedThreat.attackerInfo && (
                <div>
                  <h3 className="font-semibold text-text-primary mb-2">Attacker Information</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {selectedThreat.attackerInfo.name && (
                      <div>
                        <span className="text-text-secondary">Name:</span>
                        <span className="ml-2 text-text-primary">
                          {selectedThreat.attackerInfo.name}
                        </span>
                      </div>
                    )}
                    {selectedThreat.attackerInfo.group && (
                      <div>
                        <span className="text-text-secondary">Group:</span>
                        <span className="ml-2 text-text-primary">
                          {selectedThreat.attackerInfo.group}
                        </span>
                      </div>
                    )}
                    {selectedThreat.attackerInfo.country && (
                      <div>
                        <span className="text-text-secondary">Country:</span>
                        <span className="ml-2 text-text-primary">
                          {selectedThreat.attackerInfo.country}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* References */}
              {selectedThreat.references && selectedThreat.references.length > 0 && (
                <div>
                  <h3 className="font-semibold text-text-primary mb-2">References</h3>
                  <div className="space-y-1">
                    {selectedThreat.references.map((ref, index) => (
                      <a
                        key={index}
                        href={ref}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-500 hover:underline block"
                      >
                        {ref}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ThreatTable;
