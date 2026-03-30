import React from 'react';
import { Outlet } from 'react-router-dom';
import PageWrapper from '../PageWrapper';
import { useAuth } from '../../hooks/useAuth';

const DashboardLayout: React.FC = () => {
  const { user } = useAuth();

  return (
    <PageWrapper>
      <div className="pt-16 min-h-screen bg-gray-50">
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2 flex items-center justify-end text-sm text-gray-800">
            <span className="flex items-center font-medium">
              {user?.name ?? 'User'}
              {user?.is_beta === true && (
                <span
                  title="Beta tester — Professional tier access"
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800 ml-2"
                >
                  BETA
                </span>
              )}
            </span>
          </div>
        </div>
        <Outlet />
      </div>
    </PageWrapper>
  );
};

export default DashboardLayout;
