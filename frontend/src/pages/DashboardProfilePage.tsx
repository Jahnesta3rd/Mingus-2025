import React from 'react';
import SettingsPage from './SettingsPage';
import { useAuth } from '../hooks/useAuth';

const DashboardProfilePage: React.FC = () => {
  const { user } = useAuth();
  return <SettingsPage userId={user?.id ?? 'demo-user-123'} />;
};

export default DashboardProfilePage;
