import { useState, useEffect, useRef } from 'react';
import type { KeyboardEvent } from 'react';
import type { VulnerabilityFilters } from '@/types/api';
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
import { createDefaultFilterState, serializeFilters, type FilterState, type EpssBucket } from '@/config/filterSchema';

interface FilterPanelProps {
  onFilterChange: (filters: VulnerabilityFilters) => void;
}

const FilterPanel = ({ onFilterChange }: FilterPanelProps) => {
  const [filters, setFilters] = useState<FilterState>(() => createDefaultFilterState());
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
  const threatIntelOptions = [
    { label: 'Metasploit', value: 'metasploit' },
    { label: 'Nuclei', value: 'nuclei' },
    { label: 'RecordFuture', value: 'recordfuture' },
  ];
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

  const handleFilterChange = <K extends keyof FilterState>(field: K, value: FilterState[K]) => {
    setFilters((prev) => ({ ...prev, [field]: value }));
  };

  const handleVendorToggle = (vendor: string) => {
    const isSelected = filters.vendors.includes(vendor);
    const newVendors = isSelected
      ? filters.vendors.filter(v => v !== vendor)
      : [...filters.vendors, vendor];

    handleFilterChange('vendors', newVendors);
  };

  const getSelectedVendors = (): string[] => {
    return filters.vendors;
  };

  const handleThreatIntelToggle = (value: string) => {
    const isSelected = filters.threatIntel.includes(value);
    const newSources = isSelected
      ? filters.threatIntel.filter((item) => item !== value)
      : [...filters.threatIntel, value];
    handleFilterChange('threatIntel', newSources);
  };

  const getSelectedThreatIntel = (): string[] => {
    return filters.threatIntel;
  };

  const handleEpssBucketChange = (bucket: EpssBucket) => {
    handleFilterChange('epssBucket', bucket);
  };

  const applyFilters = () => {
    onFilterChange(serializeFilters(filters));
  };

  const clearFilters = () => {
    const clearedFilters = createDefaultFilterState();
    setFilters(clearedFilters);
    onFilterChange(serializeFilters(clearedFilters));
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
              value={filters.cveId}
              onChange={(e) => handleFilterChange('cveId', e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search CVE ID"
              className="h-8 text-xs"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-secondary">Device Name</label>
            <Input
              type="text"
              value={filters.deviceName}
              onChange={(e) => handleFilterChange('deviceName', e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search device name"
              className="h-8 text-xs"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-secondary">Severity</label>
            <Select
              value={filters.severity}
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
              value={filters.status}
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
              value={filters.platform}
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
              value={filters.cvssMin}
              onChange={(e) => handleFilterChange('cvssMin', e.target.value)}
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
              value={filters.cvssMax}
              onChange={(e) => handleFilterChange('cvssMax', e.target.value)}
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
              value={filters.epssBucket}
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
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-secondary">KEV</label>
            <Select
              value={filters.kev}
              onValueChange={(value) => handleFilterChange('kev', value as FilterState['kev'])}
            >
              <SelectTrigger className="h-8 text-xs">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="true">True</SelectItem>
                <SelectItem value="false">False</SelectItem>
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
