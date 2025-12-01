import type { ReactNode } from 'react';

export const renderSeverityBadge = (severity?: string): ReactNode => {
  if (!severity) {
    return <span className="text-xs text-text-tertiary">Unknown</span>;
  }

  const normalized = severity.toLowerCase();
  const badgeClasses: Record<string, string> = {
    critical: 'bg-red-500/10 text-red-500 border-red-500/30',
    high: 'bg-orange-500/10 text-orange-500 border-orange-500/30',
    medium: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/30',
    low: 'bg-green-500/10 text-green-500 border-green-500/30',
  };

  const isSeverityKey = (value: string): value is keyof typeof badgeClasses =>
    value in badgeClasses;

  const className = isSeverityKey(normalized)
    ? badgeClasses[normalized]
    : 'bg-gray-500/10 text-gray-500 border-gray-500/30';

  return (
    <span className={`px-2 py-1 text-xs rounded-full border ${className}`}>
      {severity}
    </span>
  );
};
