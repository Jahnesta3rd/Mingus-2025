import React, { useState, useMemo } from 'react';
import {
  ActiveSessionsProps,
  Session,
  SessionFilter,
  SessionStats,
  SessionCardProps
} from '@/types/sessionManagement';
import { SessionCard } from './SessionCard';
import { FilterPanel } from './FilterPanel';
import { BulkActions } from './BulkActions';
import { LoadingSkeleton } from './LoadingSkeleton';
import { OfflineIndicator } from './OfflineIndicator';
import { LocationMap } from './LocationMap';

const ActiveSessions: React.FC<ActiveSessionsProps> = ({
  sessions,
  onTerminateSession,
  onTerminateMultipleSessions,
  onTrustSession,
  onUntrustSession,
  onSelectSession,
  onSelectAllSessions,
  selectedSessions,
  isLoading,
  filters,
  onUpdateFilters,
  stats
}) => {
  const [viewMode, setViewMode] = useState<'list' | 'grid' | 'map'>('list');
  const [showMap, setShowMap] = useState(false);
  const [sortBy, setSortBy] = useState<'lastActivity' | 'securityScore' | 'riskLevel' | 'createdAt'>('lastActivity');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const filteredAndSortedSessions = useMemo(() => {
    let filtered = sessions.filter(session => {
      if (filters.deviceType && session.deviceType !== filters.deviceType) return false;
      if (filters.riskLevel && session.riskLevel !== filters.riskLevel) return false;
      if (filters.location && !session.location.city.toLowerCase().includes(filters.location.toLowerCase())) return false;
      if (filters.isTrusted !== undefined && session.isTrusted !== filters.isTrusted) return false;
      if (filters.isActive !== undefined && session.isActive !== filters.isActive) return false;
      if (filters.searchTerm) {
        const searchLower = filters.searchTerm.toLowerCase();
        return (
          session.deviceName.toLowerCase().includes(searchLower) ||
          session.ipAddress.includes(searchLower) ||
          session.location.city.toLowerCase().includes(searchLower) ||
          session.browser?.toLowerCase().includes(searchLower) ||
          session.operatingSystem?.toLowerCase().includes(searchLower)
        );
      }
      return true;
    });

    // Sort sessions
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'lastActivity':
          aValue = new Date(a.lastActivity).getTime();
          bValue = new Date(b.lastActivity).getTime();
          break;
        case 'securityScore':
          aValue = a.securityScore;
          bValue = b.securityScore;
          break;
        case 'riskLevel':
          const riskOrder = { low: 0, medium: 1, high: 2, critical: 3 };
          aValue = riskOrder[a.riskLevel];
          bValue = riskOrder[b.riskLevel];
          break;
        case 'createdAt':
          aValue = new Date(a.createdAt).getTime();
          bValue = new Date(b.createdAt).getTime();
          break;
        default:
          return 0;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [sessions, filters, sortBy, sortOrder]);

  const handleSelectAll = (selected: boolean) => {
    onSelectAllSessions(selected);
  };

  const handleBulkTerminate = async (reason?: string) => {
    if (selectedSessions.length > 0) {
      await onTerminateMultipleSessions(selectedSessions, reason);
    }
  };

  const handleBulkTrust = async () => {
    for (const sessionId of selectedSessions) {
      await onTrustSession(sessionId);
    }
  };

  const handleBulkUntrust = async () => {
    for (const sessionId of selectedSessions) {
      await onUntrustSession(sessionId);
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getDeviceTypeIcon = (deviceType: string) => {
    switch (deviceType) {
      case 'mobile':
        return (
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      case 'desktop':
        return (
          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      case 'tablet':
        return (
          <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
    }
  };

  if (isLoading) {
    return <LoadingSkeleton type="session" count={5} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Active Sessions</h2>
          <p className="text-gray-600 mt-1">
            Manage your active sessions and monitor account security
          </p>
        </div>
        
        <div className="mt-4 sm:mt-0 flex items-center space-x-3">
          <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'list' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'grid' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'map' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
            </button>
          </div>
          
          <button
            onClick={() => setShowMap(!showMap)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            {showMap ? 'Hide Map' : 'Show Map'}
          </button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-500">Active Sessions</p>
              <p className="text-2xl font-bold text-gray-900">{stats.activeSessions}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mr-3">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-500">Trusted</p>
              <p className="text-2xl font-bold text-gray-900">{stats.trustedSessions}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
              <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-7.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-500">Suspicious</p>
              <p className="text-2xl font-bold text-gray-900">{stats.suspiciousSessions}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mr-3">
              <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-500">Avg Duration</p>
              <p className="text-2xl font-bold text-gray-900">{Math.round(stats.averageSessionDuration)}m</p>
            </div>
          </div>
        </div>
      </div>

      {/* Location Map */}
      {showMap && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Session Locations</h3>
            <p className="text-gray-600 text-sm">View the geographic distribution of your active sessions</p>
          </div>
          <LocationMap
            sessions={filteredAndSortedSessions}
            onSessionClick={(session) => {
              // Handle session click - could open details modal
              console.log('Session clicked:', session);
            }}
            height="400px"
          />
        </div>
      )}

      {/* Filters and Sorting */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <FilterPanel
            filters={filters}
            onUpdateFilters={onUpdateFilters}
            onClearFilters={() => {
              onUpdateFilters({
                deviceType: undefined,
                riskLevel: undefined,
                location: undefined,
                isTrusted: undefined,
                isActive: undefined,
                searchTerm: undefined,
                dateRange: undefined
              });
            }}
            onApplyFilters={() => {}}
            stats={stats}
            isLoading={false}
          />
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Sort by:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="lastActivity">Last Activity</option>
                <option value="securityScore">Security Score</option>
                <option value="riskLevel">Risk Level</option>
                <option value="createdAt">Created</option>
              </select>
            </div>
            
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
            >
              {sortOrder === 'asc' ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedSessions.length > 0 && (
        <BulkActions
          selectedSessions={selectedSessions}
          selectedDevices={[]}
          onTerminateSessions={handleBulkTerminate}
          onTrustSessions={handleBulkTrust}
          onUntrustSessions={handleBulkUntrust}
          onRemoveDevices={() => {}}
          onTrustDevices={() => {}}
          onUntrustDevices={() => {}}
          isLoading={false}
        />
      )}

      {/* Sessions List/Grid */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedSessions.length === filteredAndSortedSessions.length && filteredAndSortedSessions.length > 0}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Select All</span>
              </label>
              
              <span className="text-sm text-gray-500">
                {selectedSessions.length} of {filteredAndSortedSessions.length} selected
              </span>
            </div>
            
            <span className="text-sm text-gray-500">
              {filteredAndSortedSessions.length} sessions
            </span>
          </div>
        </div>

        {filteredAndSortedSessions.length === 0 ? (
          <div className="p-8 text-center">
            <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No sessions found</h3>
            <p className="text-gray-500">
              {filters.searchTerm || filters.deviceType || filters.riskLevel
                ? 'Try adjusting your filters or search terms'
                : 'No active sessions at the moment'}
            </p>
          </div>
        ) : (
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4' : 'divide-y divide-gray-200'}>
            {filteredAndSortedSessions.map((session) => (
              <SessionCard
                key={session.id}
                session={session}
                isSelected={selectedSessions.includes(session.id)}
                onSelect={(selected) => onSelectSession(session.id, selected)}
                onTerminate={(reason) => onTerminateSession(session.id, reason)}
                onTrust={() => onTrustSession(session.id)}
                onUntrust={() => onUntrustSession(session.id)}
                onViewDetails={() => {
                  // Handle view details - could open modal or navigate
                  console.log('View details for session:', session.id);
                }}
                showActions={true}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ActiveSessions;
