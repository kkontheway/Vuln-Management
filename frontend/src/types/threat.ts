// Threat Intelligence Types

export interface ThreatIOC {
  type: 'IP' | 'Domain' | 'FileHash';
  value: string;
}

export interface AttackerInfo {
  name?: string;
  group?: string;
  country?: string;
}

export interface ThreatIntelligence {
  id: string;
  threatType: string; // 恶意软件、APT、钓鱼、DDoS等
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  source: string; // 数据来源
  timestamp: string; // ISO 日期字符串
  description: string;
  cveIds?: string[]; // CVE 关联
  iocs: ThreatIOC[];
  attackerInfo?: AttackerInfo;
  references?: string[]; // 参考链接
}

export interface ThreatFilters {
  threatType?: string;
  severity?: string;
  source?: string;
  cveId?: string;
  iocType?: string;
  iocValue?: string;
  attacker?: string;
  dateFrom?: string;
  dateTo?: string;
}

