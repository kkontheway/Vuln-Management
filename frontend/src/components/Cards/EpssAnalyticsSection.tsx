import { useMemo } from 'react';
import { PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import type { ChartData, AutopatchEpssCoverage } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const EPSS_BUCKETS = [
  { key: 'low', label: 'Low (0-0.5)', color: '#93C5FD' },
  { key: 'medium', label: 'Medium (0.5-0.8)', color: '#FDBA74' },
  { key: 'high', label: 'High (0.8-0.90)', color: '#F472B6' },
  { key: 'critical', label: 'Critical (>0.90)', color: '#DC2626' },
] as const;

const AUTOPATCH_PIE_COLORS = ['#10B981', '#475569'];

interface EpssAnalyticsSectionProps {
  data: ChartData[];
  autopatchCoverage?: AutopatchEpssCoverage;
}

const EpssAnalyticsSection = ({ data, autopatchCoverage }: EpssAnalyticsSectionProps) => {
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

  const autopatchPieData = useMemo(() => {
    if (!autopatchCoverage) {
      return [];
    }
    return EPSS_BUCKETS.map((bucket) => {
      const coverage = autopatchCoverage[bucket.key];
      const covered = coverage?.covered ?? 0;
      const notCovered = coverage?.not_covered ?? 0;
      return {
        key: bucket.key,
        label: bucket.label,
        color: bucket.color,
        data: [
          { name: 'Covered', value: covered },
          { name: 'Not Covered', value: notCovered },
        ],
        total: covered + notCovered,
      };
    });
  }, [autopatchCoverage]);

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
        {autopatchPieData.length > 0 && (
          <div className="mt-6">
            <div className="mb-3 text-sm font-semibold uppercase tracking-wide text-text-secondary">
              Autopatch Coverage Within EPSS Levels
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
              {autopatchPieData.map((bucket) => (
                <div
                  key={`autopatch-${bucket.key}`}
                  className="rounded-2xl border border-glass-border bg-glass-bg/40 p-4"
                >
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-text-secondary">
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: bucket.color }}
                    />
                    {bucket.label}
                  </div>
                  <div className="mt-4 h-32">
                    {bucket.total > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <RechartsPieChart>
                          <Pie
                            data={bucket.data}
                            dataKey="value"
                            innerRadius={24}
                            outerRadius={40}
                            paddingAngle={2}
                          >
                            {bucket.data.map((_, index) => (
                              <Cell
                                key={`autopatch-${bucket.key}-${index}`}
                                fill={AUTOPATCH_PIE_COLORS[index % AUTOPATCH_PIE_COLORS.length]}
                              />
                            ))}
                          </Pie>
                        </RechartsPieChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex h-full items-center justify-center text-xs text-text-secondary">
                        No data
                      </div>
                    )}
                  </div>
                  <div className="mt-2 text-xs text-text-secondary">
                    Covered: {bucket.data[0].value.toLocaleString('en-US')} · Not Covered:{' '}
                    {bucket.data[1].value.toLocaleString('en-US')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default EpssAnalyticsSection;
