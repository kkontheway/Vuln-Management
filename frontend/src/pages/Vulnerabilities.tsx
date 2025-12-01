import { useState } from 'react';
import Header from '../components/Header/Header';
import FilterPanel from '../components/FilterPanel/FilterPanel';
import VulnerabilityTable from '../components/Table/VulnerabilityTable';
import type { VulnerabilityFilters } from '@/types/api';

const Vulnerabilities = () => {
  const [filters, setFilters] = useState<VulnerabilityFilters>({});

  const handleFilterChange = (newFilters: VulnerabilityFilters) => {
    setFilters(newFilters);
  };

  return (
    <div className="space-y-6">
      <Header />
      <div className="mt-6 space-y-6 max-w-full overflow-x-auto">
        <FilterPanel onFilterChange={handleFilterChange} />
        <VulnerabilityTable filters={filters} />
      </div>
    </div>
  );
};

export default Vulnerabilities;
