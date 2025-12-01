import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { CHART_COLORS } from '@/utils/constants';
import type { AgeDistributionData } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface BarChartProps {
  data: AgeDistributionData;
  title: string;
}

const BarChart = ({ data, title }: BarChartProps) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <Card className="glass-panel">
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-[220px] items-center justify-center text-text-tertiary">
            No data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Transform data for Recharts stacked bar chart
  const ageRanges = ['< 30天', '30-60天', '60-90天', '> 90天'];
  const chartData = ageRanges.map((ageRange) => {
    const rangeData = data[ageRange] || {};
    return {
      ageRange,
      Critical: rangeData.Critical || 0,
      High: rangeData.High || 0,
      Medium: rangeData.Medium || 0,
      Low: rangeData.Low || 0,
      Other: rangeData.Other || 0,
    };
  });

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <RechartsBarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 0, 0, 0.1)" />
            <XAxis dataKey="ageRange" stroke="rgba(26, 26, 26, 0.7)" />
            <YAxis stroke="rgba(26, 26, 26, 0.7)" />
            <Tooltip />
            <Legend />
            <Bar dataKey="Critical" stackId="a" fill={CHART_COLORS.critical} name="高危" />
            <Bar dataKey="High" stackId="a" fill={CHART_COLORS.high} name="高危" />
            <Bar dataKey="Medium" stackId="a" fill={CHART_COLORS.medium} name="中危" />
            <Bar dataKey="Low" stackId="a" fill={CHART_COLORS.low} name="低危" />
            <Bar dataKey="Other" stackId="a" fill="#9CA3AF" name="其他" />
          </RechartsBarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default BarChart;

