import { useState, useEffect, useCallback } from 'react';
import Header from '../components/Header/Header';
import PieChart from '../components/Charts/PieChart';
import BarChart from '../components/Charts/BarChart';
import SeverityTrendTabs from '../components/Charts/SeverityTrendTabs';
import VulnerabilityTrendCard from '../components/Cards/VulnerabilityTrendCard';
import FixedVulnerabilitiesTable from '../components/Tables/FixedVulnerabilitiesTable';
import PatchThisTable, { DeviceTagFilter } from '../components/Tables/PatchThisTable';
import EpssAnalyticsSection from '../components/Cards/EpssAnalyticsSection';
import IntelligenceFeedOverlapChart from '../components/Charts/IntelligenceFeedOverlapChart';
import apiService from '../services/api';
import type {
  ChartData,
  SnapshotsTrendResponse,
  AgeDistributionData,
  AutopatchCoverage,
  AutopatchEpssCoverage,
  FixedVulnerability,
  Vulnerability,
  TrendSeries,
} from '@/types/api';

const Dashboard = () => {
  const [statistics, setStatistics] = useState<{
    severity: ChartData[];
    age_distribution: AgeDistributionData;
    exploitability_ratio: ChartData[];
    autopatch_coverage?: AutopatchCoverage;
    autopatch_epss_coverage?: AutopatchEpssCoverage;
    new_vulnerabilities_7days?: number;
    epss_distribution: ChartData[];
    intel_feed_overlap: ChartData[];
  }>({
    severity: [],
    age_distribution: {},
    exploitability_ratio: [],
    autopatch_coverage: undefined,
    autopatch_epss_coverage: undefined,
    new_vulnerabilities_7days: 0,
    epss_distribution: [],
    intel_feed_overlap: [],
  });
  const [trendData, setTrendData] = useState<SnapshotsTrendResponse['trend']>([]);
  const [trendPeriods, setTrendPeriods] = useState<TrendSeries>({ week: [], month: [], year: [] });
  const [fixedVulnerabilities, setFixedVulnerabilities] = useState<FixedVulnerability[]>([]);
  const [patchThisThirdParty, setPatchThisThirdParty] = useState<Vulnerability[]>([]);
  const [patchThisMicrosoft, setPatchThisMicrosoft] = useState<Vulnerability[]>([]);
  const [activePatchDeviceTag, setActivePatchDeviceTag] = useState<DeviceTagFilter>('victrex');

  const loadData = useCallback(async () => {
    try {
      const [
        statsResponse,
        trendResponse,
        fixedResponse,
        patchThirdResponse,
        patchMsResponse,
        dashboardTrendsResponse,
      ] = await Promise.all([
        apiService.getStatistics(),
        apiService.getSnapshotsTrend(),
        apiService.getFixedVulnerabilities(50),
        apiService.getPatchThisVulnerabilities({ vendorScope: 'third_party' }),
        apiService.getPatchThisVulnerabilities({ vendorScope: 'microsoft' }),
        apiService.getDashboardTrends(),
      ]);

      setStatistics({
        severity: statsResponse.severity || [],
        age_distribution: statsResponse.age_distribution || {},
        exploitability_ratio: statsResponse.exploitability_ratio || [],
        autopatch_coverage: statsResponse.autopatch_coverage,
        autopatch_epss_coverage: statsResponse.autopatch_epss_coverage,
        new_vulnerabilities_7days: statsResponse.new_vulnerabilities_7days || 0,
        epss_distribution: statsResponse.epss_distribution || [],
        intel_feed_overlap: statsResponse.intel_feed_overlap || [],
      });
      setTrendData(trendResponse.trend || []);
      setTrendPeriods(dashboardTrendsResponse);
      setFixedVulnerabilities(fixedResponse.data || []);
      setPatchThisThirdParty(patchThirdResponse.data || []);
      setPatchThisMicrosoft(patchMsResponse.data || []);
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
          <VulnerabilityTrendCard
            title="New Vulnerabilities (7 Days)"
            description="Newly detected CVEs across the past week"
            data={trendData}
            totalNew={statistics.new_vulnerabilities_7days}
          />
        </div>

        <PatchThisTable
          data={patchThisThirdParty}
          title="PatchThis (3rd Party)"
          activeDeviceTag={activePatchDeviceTag}
          onDeviceTagChange={setActivePatchDeviceTag}
        />
        <PatchThisTable
          data={patchThisMicrosoft}
          title="PatchThis (MS)"
          activeDeviceTag={activePatchDeviceTag}
          onDeviceTagChange={setActivePatchDeviceTag}
        />

        <FixedVulnerabilitiesTable data={fixedVulnerabilities} limit={10} />

        <EpssAnalyticsSection
          data={statistics.epss_distribution}
          autopatchCoverage={statistics.autopatch_epss_coverage}
        />

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

        <SeverityTrendTabs data={trendPeriods} />
        <BarChart data={statistics.age_distribution} title="Vulnerability Age Distribution" />
        <PieChart data={statistics.exploitability_ratio} title="Exploitable vs Theoretical Risk" />
        <IntelligenceFeedOverlapChart data={statistics.intel_feed_overlap} />
      </div>
    </div>
  );
};

export default Dashboard;
