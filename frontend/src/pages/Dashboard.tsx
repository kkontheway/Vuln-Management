import { useState, useEffect, useCallback } from 'react';
import Header from '../components/Header/Header';
import PieChart from '../components/Charts/PieChart';
import LineChart from '../components/Charts/LineChart';
import BarChart from '../components/Charts/BarChart';
import StatCard from '../components/Cards/StatCard';
import FixedVulnerabilitiesTable from '../components/Tables/FixedVulnerabilitiesTable';
import apiService from '../services/api';
import type { ChartData, SnapshotsTrendResponse, AgeDistributionData, AutopatchCoverage, FixedVulnerability } from '@/types/api';

const Dashboard = () => {
  const [statistics, setStatistics] = useState<{
    severity: ChartData[];
    age_distribution: AgeDistributionData;
    exploitability_ratio: ChartData[];
    autopatch_coverage?: AutopatchCoverage;
    new_vulnerabilities_7days?: number;
  }>({
    severity: [],
    age_distribution: {},
    exploitability_ratio: [],
    autopatch_coverage: undefined,
    new_vulnerabilities_7days: 0,
  });
  const [trendData, setTrendData] = useState<SnapshotsTrendResponse['trend']>([]);
  const [fixedVulnerabilities, setFixedVulnerabilities] = useState<FixedVulnerability[]>([]);

  const loadData = useCallback(async () => {
    try {
      const [statsResponse, trendResponse, fixedResponse] = await Promise.all([
        apiService.getStatistics(),
        apiService.getSnapshotsTrend(),
        apiService.getFixedVulnerabilities(50),
      ]);

      setStatistics({
        severity: statsResponse.severity || [],
        age_distribution: statsResponse.age_distribution || {},
        exploitability_ratio: statsResponse.exploitability_ratio || [],
        autopatch_coverage: statsResponse.autopatch_coverage,
        new_vulnerabilities_7days: statsResponse.new_vulnerabilities_7days || 0,
      });
      setTrendData(trendResponse.trend || []);
      setFixedVulnerabilities(fixedResponse.data || []);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  // Prepare Autopatch coverage data for pie charts
  const autopatchCriticalData: ChartData[] = statistics.autopatch_coverage ? [
    { name: 'Autopatch Covered', value: statistics.autopatch_coverage.critical.covered },
    { name: 'Not Covered', value: statistics.autopatch_coverage.critical.not_covered },
  ] : [];

  const autopatchHighData: ChartData[] = statistics.autopatch_coverage ? [
    { name: 'Autopatch Covered', value: statistics.autopatch_coverage.high.covered },
    { name: 'Not Covered', value: statistics.autopatch_coverage.high.not_covered },
  ] : [];

  const autopatchMediumData: ChartData[] = statistics.autopatch_coverage ? [
    { name: 'Autopatch Covered', value: statistics.autopatch_coverage.medium.covered },
    { name: 'Not Covered', value: statistics.autopatch_coverage.medium.not_covered },
  ] : [];

  return (
    <div className="space-y-6">
      <Header />
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <PieChart data={statistics.severity} title="By Severity" />
          <StatCard
            title="New Vulnerabilities (7 Days)"
            value={statistics.new_vulnerabilities_7days || 0}
            description="Newly detected CVEs in the past 7 days"
          />
        </div>

        <FixedVulnerabilitiesTable data={fixedVulnerabilities} limit={10} />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <PieChart
            data={autopatchCriticalData}
            title="Critical - Autopatch Coverage"
          />
          <PieChart
            data={autopatchHighData}
            title="High - Autopatch Coverage"
          />
          <PieChart
            data={autopatchMediumData}
            title="Medium - Autopatch Coverage"
          />
        </div>

        <LineChart data={trendData} title="Severity Trend" />
        <BarChart data={statistics.age_distribution} title="Vulnerability Age Distribution" />
        <PieChart data={statistics.exploitability_ratio} title="Exploitable vs Theoretical Risk" />
      </div>
    </div>
  );
};

export default Dashboard;
