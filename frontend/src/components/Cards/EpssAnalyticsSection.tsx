import { useMemo } from 'react';
import type { ChartData } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const EPSS_BUCKETS = [
  { label: 'Low (0-0.5)', color: '#93C5FD' },
  { label: 'Medium (0.5-0.8)', color: '#FDBA74' },
  { label: 'High (0.8-0.90)', color: '#F472B6' },
  { label: 'Critical (>0.90)', color: '#DC2626' },
];

interface EpssAnalyticsSectionProps {
  data: ChartData[];
}

const EpssAnalyticsSection = ({ data }: EpssAnalyticsSectionProps) => {
  const total = useMemo(() => data?.reduce((sum, entry) => sum + (entry.value || 0), 0) || 0, [data]);

  const normalized = useMemo(
    () =>
      EPSS_BUCKETS.map((bucket) => {
        const match = data?.find((item) => item.name === bucket.label);
        const value = match?.value ?? 0;
        const percentage = total > 0 ? (value / total) * 100 : 0;
        return { ...bucket, value, percentage };
      }),
    [data, total],
  );

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle className="text-lg">EPSS Distribution Snapshot</CardTitle>
        <p className="text-sm text-text-secondary">
          {total.toLocaleString('en-US')} vulnerabilities with EPSS scores
        </p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          {normalized.map((bucket) => (
            <div
              key={bucket.label}
              className="rounded-2xl border border-glass-border bg-glass-bg/40 p-4"
            >
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-text-secondary">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: bucket.color }}
                />
                {bucket.label}
              </div>
              <div className="mt-2 text-2xl font-semibold text-text-primary">
                {bucket.value.toLocaleString('en-US')}
              </div>
              <div className="text-sm text-text-secondary">
                {bucket.percentage.toFixed(1)}% of vulnerabilities
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default EpssAnalyticsSection;
