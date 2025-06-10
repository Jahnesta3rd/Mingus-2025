import React from 'react';
import { TabNavigation } from './components/common/TabNavigation';
import { BaseCaseTab } from './components/dashboard/BaseCaseTab';
import { CareerGrowthTab } from './components/dashboard/CareerGrowthTab';
import { EmergencyExpensesTab } from './components/dashboard/EmergencyExpensesTab';
import { HealthImpactTab } from './components/dashboard/HealthImpactTab';
import { DashboardHeader } from './components/dashboard/DashboardHeader';
import { useDashboardStore } from './store/dashboardStore';

function App() {
  const activeTab = useDashboardStore((state) => state.activeTab);

  return (
    <div className="min-h-screen bg-gray-100">
      <DashboardHeader />
      <TabNavigation />
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'base-case' && <BaseCaseTab />}
        {activeTab === 'career-growth' && <CareerGrowthTab />}
        {activeTab === 'emergency-expenses' && <EmergencyExpensesTab />}
        {activeTab === 'health-impact' && <HealthImpactTab />}
      </main>
    </div>
  );
}

export default App; 