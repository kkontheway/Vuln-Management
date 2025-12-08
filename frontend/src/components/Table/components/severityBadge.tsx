import type { ReactNode } from 'react';

const knownSeverities = ["critical", "high", "medium", "low"] as const;
type KnownSeverity = (typeof knownSeverities)[number];

const badgeClasses: Record<KnownSeverity, string> = {
  critical: 'bg-red-500/10 text-red-500 border-red-500/30',
  high: 'bg-orange-500/10 text-orange-500 border-orange-500/30',
  medium: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/30',
  low: 'bg-green-500/10 text-green-500 border-green-500/30',
};

const normalizeSeverityKey = (value: string): KnownSeverity | null => {
  const lowered = value.toLowerCase();
  const trimmed = lowered.replace(/^\d+\s*[-:]\s*/, '').trim();
  return (
    knownSeverities.find((level) => trimmed === level || trimmed.includes(level)) ||
    knownSeverities.find((level) => lowered.includes(level)) ||
    null
  );
};

export const renderSeverityBadge = (severity?: string): ReactNode => {
  if (!severity) {
    return <span className="text-xs text-text-tertiary">Unknown</span>;
  }

  const normalizedKey = normalizeSeverityKey(severity);
  const className = normalizedKey
    ? badgeClasses[normalizedKey]
    : 'bg-gray-500/10 text-gray-500 border-gray-500/30';

  const formatLabel = (value: string) => {
    if (normalizedKey) {
      return normalizedKey.charAt(0).toUpperCase() + normalizedKey.slice(1);
    }

    // Remove numeric prefixes like "1 - Critical" before falling back
    const cleaned = value.replace(/^\d+\s*[-:]\s*/, '').trim();
    return cleaned || value;
  };

  return (
    <span className={`px-2 py-1 text-xs rounded-full border ${className}`}>
      {formatLabel(severity)}
    </span>
  );
};
