import React from 'react';
import SettingsPage from './SettingsPage';
import { useAuth } from '../hooks/useAuth';

const DashboardProfilePage: React.FC = () => {
  const { user } = useAuth();
  return (
    <>
      {/* Hash target for links from roster / special dates (full editor lives in profile setup flows). */}
      <div id="important-dates" className="scroll-mt-20" aria-hidden />
      <SettingsPage userId={user?.id ?? 'demo-user-123'} />
    </>
  );
};

export default DashboardProfilePage;
