import { useState, useEffect, useRef } from 'react';
import type { KeyboardEvent } from 'react';
import apiService from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import type { VulnerabilityFilters } from '@/types/api';

interface FilterPanelProps {
  onFilterChange: (filters: VulnerabilityFilters) => void;
}

type EpssBucket = 'all' | 'low' | 'medium' | 'high' | 'critical';

const FilterPanel = ({ onFilterChange }: FilterPanelProps) => {
  const [filters, setFilters] = useState<VulnerabilityFilters>({
    cve_id: '',
    device_name: '',
    severity: '',
    status: '',
    platform: '',
    exploitability: '',
    cvss_min: '',
    cvss_max: '',
    epss_min: '',
    epss_max: '',
    threat_intel: [],
  });
  const [filterOptions, setFilterOptions] = useState<{
    severities: string[];
    platforms: string[];
    statuses: string[];
    cve_ids: string[];
    device_names: string[];
    vendors: string[];
  }>({
    severities: [],
    platforms: [],
    statuses: [],
    cve_ids: [],
    device_names: [],
    vendors: [],
  });
  const [vendorDropdownOpen, setVendorDropdownOpen] = useState(false);
  const vendorDropdownRef = useRef<HTMLDivElement>(null);
  const [threatIntelDropdownOpen, setThreatIntelDropdownOpen] = useState(false);
  const threatIntelDropdownRef = useRef<HTMLDivElement>(null);
  const [epssBucket, setEpssBucket] = useState<EpssBucket>('all');
  const threatIntelOptions = [
    { label: 'Metasploit', value: 'metasploit' },
    { label: 'Nuclei', value: 'nuclei' },
    { label: 'RecordFuture', value: 'recordfuture' },
  ];
  const epssRangeMap: Record<Exclude<EpssBucket, 'all'>, { min: string; max: string }> = {
    low: { min: '0', max: '0.5' },
    medium: { min: '0.5', max: '0.8' },
    high: { min: '0.8', max: '0.9' },
    critical: { min: '0.9', max: '' },
  };

  useEffect(() => {
    void loadFilterOptions();
  }, []);

  const loadFilterOptions = async () => {
    try {
      const data = await apiService.getFilterOptions();
      setFilterOptions({
        severities: data.vulnerability_severity_level || [],
        platforms: data.os_platform || [],
        statuses: data.status || [],
        cve_ids: [],
        device_names: [],
        vendors: data.software_vendor || [],
      });
    } catch (error) {
      console.error('Failed to load filter options:', error);
      // 设置默认空数组以避免UI错误
      setFilterOptions({
        severities: [],
        platforms: [],
        statuses: [],
        cve_ids: [],
        device_names: [],
        vendors: [],
      });
    }
  };

  const handleFilterChange = (field: keyof VulnerabilityFilters, value: string | string[]) => {
    const newFilters = { ...filters, [field]: value };
    setFilters(newFilters);
  };

  const handleVendorToggle = (vendor: string) => {
    const currentVendors = Array.isArray(filters.software_vendor)
      ? filters.software_vendor
      : filters.software_vendor ? [filters.software_vendor] : [];

    const isSelected = currentVendors.includes(vendor);
    const newVendors = isSelected
      ? currentVendors.filter(v => v !== vendor)
      : [...currentVendors, vendor];

    handleFilterChange('software_vendor', newVendors.length > 0 ? newVendors : '');
  };

  const getSelectedVendors = (): string[] => {
    if (Array.isArray(filters.software_vendor)) {
      return filters.software_vendor;
    }
    return filters.software_vendor ? [filters.software_vendor] : [];
  };

  const handleThreatIntelToggle = (value: string) => {
    const currentSources = getSelectedThreatIntel();
    const isSelected = currentSources.includes(value);
    const newSources = isSelected
      ? currentSources.filter((item) => item !== value)
      : [...currentSources, value];
    handleFilterChange('threat_intel', newSources.length > 0 ? newSources : '');
  };

  const getSelectedThreatIntel = (): string[] => {
    if (Array.isArray(filters.threat_intel)) {
      return filters.threat_intel;
    }
    return filters.threat_intel ? [filters.threat_intel] : [];
  };

  const handleEpssBucketChange = (bucket: EpssBucket) => {
    setEpssBucket(bucket);
    if (bucket === 'all') {
      handleFilterChange('epss_min', '');
      handleFilterChange('epss_max', '');
      return;
    }
    const range = epssRangeMap[bucket];
    handleFilterChange('epss_min', range.min);
    handleFilterChange('epss_max', range.max);
  };

  const applyFilters = () => {
    // Convert 'all' values back to empty strings for API
    const apiFilters: VulnerabilityFilters = {
      ...filters,
      severity: filters.severity === 'all' ? '' : filters.severity,
      status: filters.status === 'all' ? '' : filters.status,
      platform: filters.platform === 'all' ? '' : filters.platform,
      // Keep software_vendor as array if it's an array, or convert to empty string if empty
      software_vendor: Array.isArray(filters.software_vendor) && filters.software_vendor.length > 0
        ? filters.software_vendor
        : filters.software_vendor || '',
      threat_intel: Array.isArray(filters.threat_intel) && filters.threat_intel.length > 0
        ? filters.threat_intel
        : filters.threat_intel || '',
    };
    onFilterChange(apiFilters);
  };

  const clearFilters = () => {
    const clearedFilters: VulnerabilityFilters = {
      cve_id: '',
      device_name: '',
      severity: '',
      status: '',
      platform: '',
      exploitability: '',
      cvss_min: '',
      cvss_max: '',
      epss_min: '',
      epss_max: '',
      software_vendor: '',
      threat_intel: [],
    };
    setFilters(clearedFilters);
    setEpssBucket('all');
    onFilterChange(clearedFilters);
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (vendorDropdownRef.current && !vendorDropdownRef.current.contains(target)) {
        setVendorDropdownOpen(false);
      }
      if (threatIntelDropdownRef.current && !threatIntelDropdownRef.current.contains(target)) {
        setThreatIntelDropdownOpen(false);
      }
    };

    if (vendorDropdownOpen || threatIntelDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [vendorDropdownOpen, threatIntelDropdownOpen]);

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      applyFilters();
    }
  };

  return (
    <Card className="glass-panel">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold">Filters</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 p-4 pt-0">
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label className="text-xs font-medium text-text-secondary">CVE ID</label>
            <Input
              type="text"
              value={filters.cve_id || ''}
              onChange={(e) => handleFilterChange('cve_id', e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search CVE ID"
              className="h-8 text-xs"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-secondary">Device Name</label>
            <Input
              type="text"
              value={filters.device_name || ''}
              onChange={(e) => handleFilterChange('device_name', e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search device name"
              className="h-8 text-xs"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-secondary">Severity</label>
            <Select
              value={filters.severity || 'all'}
              onValueChange={(value) => handleFilterChange('severity', value)}
            >
              <SelectTrigger className="h-8 text-xs">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {filterOptions.severities.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-secondary">Status</label>
            <Select
              value={filters.status || 'all'}
              onValueChange={(value) => handleFilterChange('status', value)}
            >
              <SelectTrigger className="h-8 text-xs">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {filterOptions.statuses.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-secondary">OS Platform</label>
            <Select
              value={filters.platform || 'all'}
              onValueChange={(value) => handleFilterChange('platform', value)}
            >
              <SelectTrigger className="h-8 text-xs">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {filterOptions.platforms.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-secondary">CVSS Min Score</label>
            <Input
              type="number"
              value={filters.cvss_min || ''}
              onChange={(e) => handleFilterChange('cvss_min', e.target.value)}
              min="0"
              max="10"
              step="0.1"
              placeholder="0.0"
              className="h-8 text-xs"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-secondary">CVSS Max Score</label>
            <Input
              type="number"
              value={filters.cvss_max || ''}
              onChange={(e) => handleFilterChange('cvss_max', e.target.value)}
              min="0"
              max="10"
              step="0.1"
              placeholder="10.0"
              className="h-8 text-xs"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-secondary">EPSS Score</label>
            <Select
              value={epssBucket}
              onValueChange={(value) => handleEpssBucketChange(value as EpssBucket)}
            >
              <SelectTrigger className="h-8 text-xs">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="low">Low (0 - 0.5)</SelectItem>
                <SelectItem value="medium">Medium (0.5 - 0.8)</SelectItem>
                <SelectItem value="high">High (0.8 - 0.9)</SelectItem>
                <SelectItem value="critical">Critical (&gt; 0.9)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2 relative" ref={vendorDropdownRef}>
            <label className="text-xs font-medium text-text-secondary">Software Vendor</label>
            <Button
              type="button"
              variant="outline"
              onClick={() => setVendorDropdownOpen(!vendorDropdownOpen)}
              className="w-full justify-between h-8 text-xs bg-white text-text-primary dark:bg-[#050506] dark:text-white"
              size="sm"
            >
              <span>
                {getSelectedVendors().length > 0
                  ? `${getSelectedVendors().length} vendor(s) selected`
                  : 'Select vendors'}
              </span>
              <svg
                className={cn(
                  "h-4 w-4 transition-transform",
                  vendorDropdownOpen && "rotate-180"
                )}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </Button>
            {vendorDropdownOpen && (
              <div className="absolute z-50 w-full mt-1 rounded-lg border border-glass-border bg-white text-text-primary shadow-lg max-h-60 overflow-auto dark:bg-[#050506] dark:text-white">
                <div className="p-2 space-y-2">
                  {filterOptions.vendors.length === 0 ? (
                    <div className="text-sm text-text-secondary p-2">No vendors available</div>
                  ) : (
                    filterOptions.vendors.map((vendor) => {
                      const isSelected = getSelectedVendors().includes(vendor);
                      return (
                        <label
                          key={vendor}
                          className="flex items-center space-x-2 p-2 rounded cursor-pointer hover:bg-black/5 dark:hover:bg-white/10"
                        >
                          <Checkbox
                            checked={isSelected}
                            onCheckedChange={() => handleVendorToggle(vendor)}
                          />
                          <span className="text-sm text-text-primary flex-1">{vendor}</span>
                        </label>
                      );
                    })
                  )}
                </div>
              </div>
            )}
          </div>
          <div className="space-y-2 relative" ref={threatIntelDropdownRef}>
            <label className="text-xs font-medium text-text-secondary">Threat Intel</label>
            <Button
              type="button"
              variant="outline"
              onClick={() => setThreatIntelDropdownOpen(!threatIntelDropdownOpen)}
              className="w-full justify-between h-8 text-xs bg-white text-text-primary dark:bg-[#050506] dark:text-white"
              size="sm"
            >
              <span>
                {getSelectedThreatIntel().length > 0
                  ? `${getSelectedThreatIntel().length} source(s) selected`
                  : 'Select threat intel sources'}
              </span>
              <svg
                className={cn(
                  'h-4 w-4 transition-transform',
                  threatIntelDropdownOpen && 'rotate-180'
                )}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </Button>
            {threatIntelDropdownOpen && (
              <div className="absolute z-50 w-full mt-1 rounded-lg border border-glass-border bg-white text-text-primary shadow-lg max-h-60 overflow-auto dark:bg-[#050506] dark:text-white">
                <div className="p-2 space-y-2">
                  {threatIntelOptions.map((option) => {
                    const isSelected = getSelectedThreatIntel().includes(option.value);
                    return (
                      <label
                        key={option.value}
                        className="flex items-center space-x-2 p-2 rounded cursor-pointer hover:bg-black/5 dark:hover:bg-white/10"
                      >
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => handleThreatIntelToggle(option.value)}
                        />
                        <span className="text-sm text-text-primary flex-1">{option.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
        <div className="flex gap-2 pt-2">
          <Button onClick={applyFilters} className="flex-1 h-8 text-xs" size="sm">
            Apply Filters
          </Button>
          <Button variant="outline" onClick={clearFilters} className="flex-1 h-8 text-xs" size="sm">
            Clear Filters
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default FilterPanel;
