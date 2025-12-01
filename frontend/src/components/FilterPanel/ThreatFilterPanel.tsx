import { useState } from 'react';
import type { KeyboardEvent } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { ThreatFilters } from '@/types/threat';

interface ThreatFilterPanelProps {
  onFilterChange: (filters: ThreatFilters) => void;
}

const ThreatFilterPanel = ({ onFilterChange }: ThreatFilterPanelProps) => {
  const [filters, setFilters] = useState<ThreatFilters>({
    threatType: '',
    severity: '',
    source: '',
    cveId: '',
    iocType: '',
    iocValue: '',
    attacker: '',
    dateFrom: '',
    dateTo: '',
  });

  const threatTypes = ['APT', '恶意软件', '钓鱼', 'DDoS'];
  const severities = ['Critical', 'High', 'Medium', 'Low'];
  const sources = ['CISA', 'MalwareBazaar', 'PhishTank', 'Cloudflare', 'FireEye', 'VirusTotal', 'CrowdStrike', 'Mandiant', 'OpenPhish', 'Akamai'];
  const iocTypes = ['IP', 'Domain', 'FileHash'];

  const handleFilterChange = (field: keyof ThreatFilters, value: string) => {
    const newFilters = { ...filters, [field]: value };
    setFilters(newFilters);
  };

  const applyFilters = () => {
    // Convert 'all' values back to empty strings for filtering
    const apiFilters: ThreatFilters = {
      ...filters,
      threatType: filters.threatType === 'all' ? '' : filters.threatType,
      severity: filters.severity === 'all' ? '' : filters.severity,
      source: filters.source === 'all' ? '' : filters.source,
      iocType: filters.iocType === 'all' ? '' : filters.iocType,
    };
    onFilterChange(apiFilters);
  };

  const clearFilters = () => {
    const clearedFilters: ThreatFilters = {
      threatType: '',
      severity: '',
      source: '',
      cveId: '',
      iocType: '',
      iocValue: '',
      attacker: '',
      dateFrom: '',
      dateTo: '',
    };
    setFilters(clearedFilters);
    onFilterChange(clearedFilters);
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      applyFilters();
    }
  };

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle className="text-lg">Filters</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">Threat Type</label>
            <Select 
              value={filters.threatType || 'all'} 
              onValueChange={(value) => handleFilterChange('threatType', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {threatTypes.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">Severity</label>
            <Select 
              value={filters.severity || 'all'} 
              onValueChange={(value) => handleFilterChange('severity', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {severities.map((severity) => (
                  <SelectItem key={severity} value={severity}>
                    {severity}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">Source</label>
            <Select 
              value={filters.source || 'all'} 
              onValueChange={(value) => handleFilterChange('source', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {sources.map((source) => (
                  <SelectItem key={source} value={source}>
                    {source}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">CVE ID</label>
            <Input
              type="text"
              value={filters.cveId || ''}
              onChange={(e) => handleFilterChange('cveId', e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search CVE ID"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">IOC Type</label>
            <Select 
              value={filters.iocType || 'all'} 
              onValueChange={(value) => handleFilterChange('iocType', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {iocTypes.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">IOC Value</label>
            <Input
              type="text"
              value={filters.iocValue || ''}
              onChange={(e) => handleFilterChange('iocValue', e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search IOC (IP/Domain/Hash)"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">Attacker</label>
            <Input
              type="text"
              value={filters.attacker || ''}
              onChange={(e) => handleFilterChange('attacker', e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search attacker name/group"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">Date From</label>
            <Input
              type="date"
              value={filters.dateFrom || ''}
              onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">Date To</label>
            <Input
              type="date"
              value={filters.dateTo || ''}
              onChange={(e) => handleFilterChange('dateTo', e.target.value)}
            />
          </div>
        </div>
        <div className="flex gap-2 pt-4">
          <Button onClick={applyFilters} className="flex-1">
            Apply Filters
          </Button>
          <Button variant="outline" onClick={clearFilters} className="flex-1">
            Clear Filters
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default ThreatFilterPanel;
