import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { CHART_COLORS } from '@/utils/constants';
import type { SnapshotTrend } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface LineChartProps {
  data: SnapshotTrend[];
  title: string;
}

const LineChart = ({ data, title }: LineChartProps) => {
  if (!data || data.length === 0) {
    return (
      <Card className="glass-panel">
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-[220px] items-center justify-center text-text-tertiary">
            No snapshot data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Transform data for Recharts
  const chartData = data.map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: '2-digit', day: '2-digit' }),
    Critical: item.critical || 0,
    High: item.high || 0,
    Medium: item.medium || 0,
  }));

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <RechartsLineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 0, 0, 0.1)" />
            <XAxis dataKey="date" stroke="rgba(26, 26, 26, 0.7)" />
            <YAxis stroke="rgba(26, 26, 26, 0.7)" />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="Critical" stroke={CHART_COLORS.critical} strokeWidth={2} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="High" stroke={CHART_COLORS.high} strokeWidth={2} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="Medium" stroke={CHART_COLORS.medium} strokeWidth={2} dot={{ r: 4 }} />
          </RechartsLineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default LineChart;

