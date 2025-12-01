import { useState } from 'react';
import ThreatFilterPanel from '../components/FilterPanel/ThreatFilterPanel';
import ThreatTable from '../components/Table/ThreatTable';
import type { ThreatFilters } from '@/types/threat';

const ThreatIntelligence = () => {
  const [filters, setFilters] = useState<ThreatFilters>({});

  const handleFilterChange = (newFilters: ThreatFilters) => {
    setFilters(newFilters);
  };

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-text-primary mb-2">Threat Intelligence</h1>
        <p className="text-text-secondary">View and analyze threat intelligence data collected from the internet</p>
      </div>
      <div className="space-y-6 mt-6 max-w-full overflow-x-auto">
        <ThreatFilterPanel onFilterChange={handleFilterChange} />
        <ThreatTable filters={filters} />
      </div>
    </div>
  );
};

export default ThreatIntelligence;
