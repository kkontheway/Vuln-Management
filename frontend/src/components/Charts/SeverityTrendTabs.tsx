import { useState } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import clsx from 'clsx';
import { ResponsiveContainer, LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CHART_COLORS } from '@/utils/constants';
import type { TrendPeriod, TrendSeries } from '@/types/api';

const PERIOD_OPTIONS: { key: TrendPeriod; label: string }[] = [
  { key: 'week', label: 'Week' },
  { key: 'month', label: 'Month' },
  { key: 'year', label: 'Year' },
];

interface SeverityTrendTabsProps {
  data: TrendSeries;
}

const SeverityTrendTabs = ({ data }: SeverityTrendTabsProps) => {
  const [activeTab, setActiveTab] = useState<TrendPeriod>('week');

  const renderPeriod = (period: TrendPeriod) => {
    const points = data[period] ?? [];
    if (!points.length) {
      return (
        <div className="flex h-[260px] items-center justify-center text-text-tertiary">
          No trend data available
        </div>
      );
    }

    const hasCarry = points.some((point) => point.carry);
    const chartData = points.map((point) => ({
      date: new Date(point.date).toLocaleDateString('en-US', { month: '2-digit', day: '2-digit' }),
      Critical: point.critical ?? 0,
      High: point.high ?? 0,
      Medium: point.medium ?? 0,
    }));

    return (
      <div className="space-y-3">
        <div className="h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsLineChart data={chartData} margin={{ top: 8, right: 24, left: 8, bottom: 12 }}>
              <CartesianGrid strokeDasharray="4 4" stroke="var(--border)" opacity={0.3} />
              <XAxis dataKey="date" tickLine={false} axisLine={false} stroke="rgba(26, 26, 26, 0.7)" />
              <YAxis tickLine={false} axisLine={false} stroke="rgba(26, 26, 26, 0.7)" />
              <Tooltip contentStyle={{ borderRadius: 12, borderColor: 'var(--border)' }} />
              <Line type="monotone" dataKey="Critical" stroke={CHART_COLORS.critical} strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="High" stroke={CHART_COLORS.high} strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="Medium" stroke={CHART_COLORS.medium} strokeWidth={2} dot={{ r: 3 }} />
            </RechartsLineChart>
          </ResponsiveContainer>
        </div>
        {hasCarry && (
          <p className="text-xs text-text-tertiary">
            * Some days reuse the previous snapshot because no new snapshot was captured on that date.
          </p>
        )}
      </div>
    );
  };

  return (
    <Tabs.Root value={activeTab} onValueChange={(value) => setActiveTab(value as TrendPeriod)} className="block">
      <Card className="glass-panel">
        <CardHeader className="gap-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <CardTitle className="text-lg">Severity Trend Overview</CardTitle>
            <Tabs.List className="inline-flex rounded-full border border-border bg-card p-1 text-xs font-semibold uppercase tracking-wide">
              {PERIOD_OPTIONS.map(({ key, label }) => (
                <Tabs.Trigger
                  key={key}
                  value={key}
                  className={clsx(
                    'rounded-full px-4 py-1 transition-colors',
                    activeTab === key
                      ? 'bg-primary text-white shadow-sm'
                      : 'text-text-secondary hover:text-text-primary'
                  )}
                >
                  {label}
                </Tabs.Trigger>
              ))}
            </Tabs.List>
          </div>
          <div className="flex flex-wrap gap-4 text-xs text-text-secondary">
            <LegendSwatch label="Critical" color={CHART_COLORS.critical} />
            <LegendSwatch label="High" color={CHART_COLORS.high} />
            <LegendSwatch label="Medium" color={CHART_COLORS.medium} />
          </div>
        </CardHeader>
        <CardContent>
          {PERIOD_OPTIONS.map(({ key }) => (
            <Tabs.Content key={key} value={key} className="outline-none">
              {renderPeriod(key)}
            </Tabs.Content>
          ))}
        </CardContent>
      </Card>
    </Tabs.Root>
  );
};

const LegendSwatch = ({ label, color }: { label: string; color: string }) => (
  <span className="flex items-center gap-2">
    <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
    <span>{label}</span>
  </span>
);

export default SeverityTrendTabs;
