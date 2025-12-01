import { PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, type PieLabelRenderProps } from 'recharts';
import { PIE_CHART_COLORS } from '@/utils/constants';
import type { ChartData } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface PieChartProps {
  data: ChartData[];
  title: string;
}

const PieChart = ({ data, title }: PieChartProps) => {
  if (!data || data.length === 0) {
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

  // Transform data for Recharts
  const chartData = data.map((item) => ({
    name: item.name || 'Unknown',
    value: typeof item.value === 'number' ? item.value : Number(item.value ?? 0),
  }));

  return (
    <Card className="glass-panel">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <RechartsPieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ value }: PieLabelRenderProps) => {
                if (Array.isArray(value)) {
                  return value.join(', ');
                }
                if (typeof value === 'number') {
                  return value.toString();
                }
                if (typeof value === 'string') {
                  return value;
                }
                return '';
              }}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
            {chartData.map((_, index) => (
              <Cell key={`cell-${index}`} fill={PIE_CHART_COLORS[index % PIE_CHART_COLORS.length]} />
            ))}
            </Pie>
            <Tooltip />
            <Legend />
          </RechartsPieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default PieChart;
