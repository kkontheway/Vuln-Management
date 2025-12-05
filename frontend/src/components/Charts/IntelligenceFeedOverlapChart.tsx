import { ResponsiveContainer, PieChart, Pie } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ChartData } from '@/types/api';

const FEED_COLORS: Record<string, string> = {
  'Nuclei Only': '#60A5FA',
  'Metasploit Only': '#F87171',
  'RecordFuture Only': '#FBBF24',
  'Two Feeds': '#A78BFA',
  'Three Feeds': '#34D399',
};

interface IntelligenceFeedOverlapChartProps {
  data?: ChartData[];
}

const IntelligenceFeedOverlapChart = ({ data = [] }: IntelligenceFeedOverlapChartProps) => {
  const sanitizedData = data.map((item) => ({
    ...item,
    fill: FEED_COLORS[item.name] || '#94A3B8',
    value: typeof item.value === 'number' ? item.value : Number(item.value ?? 0),
  }));
  const hasData = sanitizedData.some((item) => item.value > 0);

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle className="text-lg">Intelligence Feed Overlap</CardTitle>
      </CardHeader>
      <CardContent>
        {hasData ? (
          <div className="flex flex-col lg:flex-row lg:items-center gap-6">
            <div className="w-full lg:w-1/2">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={sanitizedData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius="80%"
                    outerRadius="100%"
                    paddingAngle={5}
                    cornerRadius="50%"
                    isAnimationActive={false}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex-1 space-y-3">
              {sanitizedData.map((item) => (
                <div key={item.name} className="flex items-center justify-between rounded-2xl border border-glass-border px-4 py-3">
                  <div className="flex items-center gap-3">
                    <span
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: item.fill }}
                    />
                    <span className="text-sm font-medium text-text-primary">{item.name}</span>
                  </div>
                  <span className="text-sm font-semibold text-text-primary">{item.value.toLocaleString('en-US')}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex h-64 items-center justify-center text-text-tertiary">
            No data available
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default IntelligenceFeedOverlapChart;
