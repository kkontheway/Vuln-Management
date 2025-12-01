import type { ThreatIntelligence } from '@/types/threat';

export const mockThreats: ThreatIntelligence[] = [
  {
    id: '1',
    threatType: 'APT',
    severity: 'Critical',
    source: 'CISA',
    timestamp: '2024-01-15T10:30:00Z',
    description: 'Advanced Persistent Threat campaign targeting critical infrastructure. Attackers using sophisticated techniques to maintain long-term access.',
    cveIds: ['CVE-2024-1234', 'CVE-2024-5678'],
    iocs: [
      { type: 'IP', value: '192.168.1.100' },
      { type: 'Domain', value: 'malicious-example.com' },
      { type: 'FileHash', value: 'a1b2c3d4e5f6789012345678901234567890abcd' },
    ],
    attackerInfo: {
      name: 'APT29',
      group: 'Cozy Bear',
      country: 'Russia',
    },
    references: [
      'https://www.cisa.gov/news-events/cybersecurity-advisories',
      'https://www.mandiant.com/resources/reports',
    ],
  },
  {
    id: '2',
    threatType: '恶意软件',
    severity: 'High',
    source: 'MalwareBazaar',
    timestamp: '2024-01-14T15:20:00Z',
    description: 'New ransomware variant detected in the wild. Encrypts files and demands cryptocurrency payment.',
    cveIds: ['CVE-2024-2345'],
    iocs: [
      { type: 'IP', value: '10.0.0.50' },
      { type: 'FileHash', value: 'f1e2d3c4b5a6789012345678901234567890efgh' },
    ],
    attackerInfo: {
      group: 'LockBit',
    },
    references: [
      'https://bazaar.abuse.ch/',
    ],
  },
  {
    id: '3',
    threatType: '钓鱼',
    severity: 'Medium',
    source: 'PhishTank',
    timestamp: '2024-01-13T09:15:00Z',
    description: 'Phishing campaign targeting financial institutions. Emails impersonating bank security alerts.',
    iocs: [
      { type: 'Domain', value: 'fake-bank-security.com' },
      { type: 'IP', value: '172.16.0.25' },
    ],
    attackerInfo: {
      country: 'Unknown',
    },
    references: [
      'https://www.phishtank.com/',
    ],
  },
  {
    id: '4',
    threatType: 'DDoS',
    severity: 'High',
    source: 'Cloudflare',
    timestamp: '2024-01-12T14:45:00Z',
    description: 'Large-scale DDoS attack targeting multiple websites. Using botnet infrastructure.',
    iocs: [
      { type: 'IP', value: '203.0.113.10' },
      { type: 'IP', value: '203.0.113.11' },
      { type: 'IP', value: '203.0.113.12' },
      { type: 'Domain', value: 'botnet-c2.example.net' },
    ],
    attackerInfo: {
      group: 'Anonymous',
    },
    references: [
      'https://www.cloudflare.com/learning/ddos/',
    ],
  },
  {
    id: '5',
    threatType: 'APT',
    severity: 'Critical',
    source: 'FireEye',
    timestamp: '2024-01-11T11:00:00Z',
    description: 'State-sponsored APT group targeting government agencies. Using zero-day exploits.',
    cveIds: ['CVE-2024-3456', 'CVE-2024-3457'],
    iocs: [
      { type: 'FileHash', value: '9876543210abcdef9876543210abcdef98765432' },
      { type: 'Domain', value: 'apt-c2.example.org' },
      { type: 'IP', value: '198.51.100.50' },
    ],
    attackerInfo: {
      name: 'APT28',
      group: 'Fancy Bear',
      country: 'Russia',
    },
    references: [
      'https://www.fireeye.com/blog/threat-research.html',
    ],
  },
  {
    id: '6',
    threatType: '恶意软件',
    severity: 'High',
    source: 'VirusTotal',
    timestamp: '2024-01-10T16:30:00Z',
    description: 'Trojan malware disguised as legitimate software update. Steals credentials and personal information.',
    cveIds: ['CVE-2024-4567'],
    iocs: [
      { type: 'FileHash', value: '1122334455667788990011223344556677889900' },
      { type: 'Domain', value: 'malware-update.com' },
    ],
    attackerInfo: {
      country: 'China',
    },
    references: [
      'https://www.virustotal.com/',
    ],
  },
  {
    id: '7',
    threatType: '钓鱼',
    severity: 'Medium',
    source: 'OpenPhish',
    timestamp: '2024-01-09T08:20:00Z',
    description: 'Phishing emails targeting Office 365 users. Attempting to steal Microsoft credentials.',
    iocs: [
      { type: 'Domain', value: 'office365-login-fake.com' },
      { type: 'IP', value: '192.0.2.100' },
    ],
    references: [
      'https://openphish.com/',
    ],
  },
  {
    id: '8',
    threatType: 'APT',
    severity: 'Critical',
    source: 'CrowdStrike',
    timestamp: '2024-01-08T13:10:00Z',
    description: 'Advanced persistent threat targeting energy sector. Long-term espionage campaign.',
    cveIds: ['CVE-2024-5678', 'CVE-2024-5679'],
    iocs: [
      { type: 'IP', value: '198.18.0.10' },
      { type: 'Domain', value: 'apt-energy-c2.net' },
      { type: 'FileHash', value: 'abcdef1234567890abcdef1234567890abcdef12' },
    ],
    attackerInfo: {
      name: 'APT1',
      group: 'Comment Crew',
      country: 'China',
    },
    references: [
      'https://www.crowdstrike.com/blog/',
    ],
  },
  {
    id: '9',
    threatType: '恶意软件',
    severity: 'High',
    source: 'MalwareBazaar',
    timestamp: '2024-01-07T10:05:00Z',
    description: 'Banking trojan targeting mobile devices. Steals banking credentials and SMS messages.',
    iocs: [
      { type: 'FileHash', value: 'fedcba0987654321fedcba0987654321fedcba09' },
      { type: 'Domain', value: 'mobile-banking-malware.com' },
    ],
    attackerInfo: {
      group: 'Cerberus',
    },
    references: [
      'https://bazaar.abuse.ch/',
    ],
  },
  {
    id: '10',
    threatType: 'DDoS',
    severity: 'Medium',
    source: 'Akamai',
    timestamp: '2024-01-06T12:00:00Z',
    description: 'Application-layer DDoS attack targeting API endpoints. Using sophisticated request patterns.',
    iocs: [
      { type: 'IP', value: '203.0.113.20' },
      { type: 'IP', value: '203.0.113.21' },
      { type: 'Domain', value: 'ddos-botnet.net' },
    ],
    references: [
      'https://www.akamai.com/blog/security',
    ],
  },
  {
    id: '11',
    threatType: 'APT',
    severity: 'Critical',
    source: 'Mandiant',
    timestamp: '2024-01-05T09:30:00Z',
    description: 'Nation-state APT group targeting defense contractors. Exfiltrating classified information.',
    cveIds: ['CVE-2024-6789'],
    iocs: [
      { type: 'FileHash', value: '1234567890abcdef1234567890abcdef12345678' },
      { type: 'IP', value: '192.168.100.200' },
      { type: 'Domain', value: 'apt-defense-c2.org' },
    ],
    attackerInfo: {
      name: 'APT10',
      group: 'MenuPass',
      country: 'China',
    },
    references: [
      'https://www.mandiant.com/resources/reports',
    ],
  },
  {
    id: '12',
    threatType: '钓鱼',
    severity: 'Low',
    source: 'PhishTank',
    timestamp: '2024-01-04T14:15:00Z',
    description: 'Low-volume phishing campaign targeting specific individuals. Spear phishing with personalized content.',
    iocs: [
      { type: 'Domain', value: 'spear-phish-example.com' },
    ],
    attackerInfo: {
      country: 'Unknown',
    },
    references: [
      'https://www.phishtank.com/',
    ],
  },
  {
    id: '13',
    threatType: '恶意软件',
    severity: 'High',
    source: 'VirusTotal',
    timestamp: '2024-01-03T11:45:00Z',
    description: 'Cryptocurrency mining malware. Infects systems and uses resources to mine cryptocurrency.',
    cveIds: ['CVE-2024-7890'],
    iocs: [
      { type: 'FileHash', value: 'aabbccddeeff00112233445566778899aabbcc' },
      { type: 'IP', value: '10.10.10.50' },
      { type: 'Domain', value: 'mining-pool-malware.com' },
    ],
    references: [
      'https://www.virustotal.com/',
    ],
  },
  {
    id: '14',
    threatType: 'APT',
    severity: 'Critical',
    source: 'FireEye',
    timestamp: '2024-01-02T15:20:00Z',
    description: 'Supply chain attack targeting software vendors. Compromising legitimate software to distribute malware.',
    cveIds: ['CVE-2024-8901', 'CVE-2024-8902'],
    iocs: [
      { type: 'FileHash', value: '9988776655443322110099887766554433221100' },
      { type: 'Domain', value: 'supply-chain-c2.example.com' },
      { type: 'IP', value: '172.20.0.100' },
    ],
    attackerInfo: {
      name: 'APT41',
      group: 'Winnti',
      country: 'China',
    },
    references: [
      'https://www.fireeye.com/blog/threat-research.html',
    ],
  },
  {
    id: '15',
    threatType: 'DDoS',
    severity: 'High',
    source: 'Cloudflare',
    timestamp: '2024-01-01T08:00:00Z',
    description: 'Memcached amplification attack. Exploiting misconfigured Memcached servers for DDoS amplification.',
    iocs: [
      { type: 'IP', value: '203.0.113.30' },
      { type: 'IP', value: '203.0.113.31' },
      { type: 'IP', value: '203.0.113.32' },
    ],
    references: [
      'https://www.cloudflare.com/learning/ddos/',
    ],
  },
  {
    id: '16',
    threatType: '恶意软件',
    severity: 'Medium',
    source: 'MalwareBazaar',
    timestamp: '2023-12-31T17:30:00Z',
    description: 'Adware bundled with free software. Displays unwanted advertisements and collects user data.',
    iocs: [
      { type: 'FileHash', value: 'ffeeddccbbaa99887766554433221100ffeedd' },
      { type: 'Domain', value: 'adware-network.com' },
    ],
    references: [
      'https://bazaar.abuse.ch/',
    ],
  },
  {
    id: '17',
    threatType: 'APT',
    severity: 'High',
    source: 'CrowdStrike',
    timestamp: '2023-12-30T10:10:00Z',
    description: 'APT group targeting healthcare organizations. Stealing patient data and medical records.',
    cveIds: ['CVE-2024-9012'],
    iocs: [
      { type: 'IP', value: '198.51.100.75' },
      { type: 'Domain', value: 'apt-healthcare-c2.net' },
      { type: 'FileHash', value: '55667788990011223344556677889900112233' },
    ],
    attackerInfo: {
      name: 'APT12',
      group: 'IXESHE',
      country: 'China',
    },
    references: [
      'https://www.crowdstrike.com/blog/',
    ],
  },
  {
    id: '18',
    threatType: '钓鱼',
    severity: 'Medium',
    source: 'OpenPhish',
    timestamp: '2023-12-29T13:25:00Z',
    description: 'Phishing campaign targeting social media accounts. Attempting to steal login credentials.',
    iocs: [
      { type: 'Domain', value: 'fake-social-login.com' },
      { type: 'IP', value: '192.0.2.200' },
    ],
    references: [
      'https://openphish.com/',
    ],
  },
  {
    id: '19',
    threatType: '恶意软件',
    severity: 'Critical',
    source: 'VirusTotal',
    timestamp: '2023-12-28T09:50:00Z',
    description: 'Worm malware spreading through network shares. Automatically infects connected systems.',
    cveIds: ['CVE-2024-0123', 'CVE-2024-0124'],
    iocs: [
      { type: 'FileHash', value: '1122334455667788990011223344556677889900aa' },
      { type: 'IP', value: '10.0.0.100' },
      { type: 'Domain', value: 'worm-c2.example.net' },
    ],
    attackerInfo: {
      country: 'North Korea',
    },
    references: [
      'https://www.virustotal.com/',
    ],
  },
  {
    id: '20',
    threatType: 'APT',
    severity: 'Critical',
    source: 'Mandiant',
    timestamp: '2023-12-27T14:40:00Z',
    description: 'Nation-state APT targeting critical infrastructure. Using zero-day exploits and custom malware.',
    cveIds: ['CVE-2024-1234', 'CVE-2024-1235', 'CVE-2024-1236'],
    iocs: [
      { type: 'FileHash', value: 'bbccddeeff00112233445566778899aabbccdd' },
      { type: 'IP', value: '198.18.0.50' },
      { type: 'Domain', value: 'apt-critical-infra-c2.org' },
    ],
    attackerInfo: {
      name: 'APT33',
      group: 'Elfin',
      country: 'Iran',
    },
    references: [
      'https://www.mandiant.com/resources/reports',
    ],
  },
];

