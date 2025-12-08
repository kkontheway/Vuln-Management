import type { VulnerabilityFilters } from '@/types/api';

export type EpssBucket = 'all' | 'low' | 'medium' | 'high' | 'critical';

export interface FilterState {
  cveId: string;
  deviceName: string;
  severity: string;
  status: string;
  platform: string;
  cvssMin: string;
  cvssMax: string;
  epssBucket: EpssBucket;
  kev: 'all' | 'true' | 'false';
  vendors: string[];
  threatIntel: string[];
}

export const EPSS_BUCKET_RANGES: Record<Exclude<EpssBucket, 'all'>, { min: string; max: string }> = {
  low: { min: '0', max: '0.5' },
  medium: { min: '0.5', max: '0.8' },
  high: { min: '0.8', max: '0.9' },
  critical: { min: '0.9', max: '' },
};

export const createDefaultFilterState = (): FilterState => ({
  cveId: '',
  deviceName: '',
  severity: 'all',
  status: 'all',
  platform: 'all',
  cvssMin: '',
  cvssMax: '',
  epssBucket: 'all',
  kev: 'all',
  vendors: [],
  threatIntel: [],
});

export const serializeFilters = (state: FilterState): VulnerabilityFilters => {
  const payload: VulnerabilityFilters = {};

  if (state.cveId.trim()) {
    payload.cve_id = state.cveId.trim();
  }
  if (state.deviceName.trim()) {
    payload.device_name = state.deviceName.trim();
  }
  if (state.severity && state.severity !== 'all') {
    payload.vulnerability_severity_level = state.severity;
  }
  if (state.status && state.status !== 'all') {
    payload.status = state.status;
  }
  if (state.platform && state.platform !== 'all') {
    payload.os_platform = state.platform;
  }
  if (state.cvssMin) {
    payload.cvss_min = state.cvssMin;
  }
  if (state.cvssMax) {
    payload.cvss_max = state.cvssMax;
  }
  if (state.epssBucket !== 'all') {
    const range = EPSS_BUCKET_RANGES[state.epssBucket as Exclude<EpssBucket, 'all'>];
    payload.epss_min = range.min;
    payload.epss_max = range.max;
    if (!range.max) {
      delete payload.epss_max;
    }
  }
  if (state.kev !== 'all') {
    payload.cve_public_exploit = state.kev;
  }
  if (state.vendors.length > 0) {
    payload.software_vendor = state.vendors;
  }
  if (state.threatIntel.length > 0) {
    payload.threat_intel = state.threatIntel;
  }

  return payload;
};
