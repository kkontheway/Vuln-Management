import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { formatNumber } from '@/utils/formatters';

interface StatCardProps {
    title: string;
    value: number | string;
    description?: string;
    className?: string;
}

const StatCard = ({ title, value, description, className }: StatCardProps) => {
    const displayValue = typeof value === 'number' ? formatNumber(value) : value;

    return (
        <Card className={`glass-panel ${className || ''}`}>
            <CardHeader>
                <CardTitle className="text-lg">{title}</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex flex-col items-center justify-center h-[180px]">
                    <div className="text-5xl font-semibold text-text-primary mb-2" style={{ letterSpacing: '-0.03em' }}>
                        {displayValue}
                    </div>
                    {description && (
                        <div className="text-sm text-text-secondary text-center mt-2">
                            {description}
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
};

export default StatCard;

