import React from 'react';
import { Outlet } from 'react-router-dom';
import PageWrapper from '../PageWrapper';

const DashboardLayout: React.FC = () => {
  return (
    <PageWrapper>
      <Outlet />
    </PageWrapper>
  );
};

export default DashboardLayout;
