import React, { useState, useMemo } from 'react';
import {
  DeviceManagementProps,
  Device,
  DeviceCardProps
} from '@/types/sessionManagement';
import { DeviceCard } from './DeviceCard';
import { LoadingSkeleton } from './LoadingSkeleton';
import { AddDeviceModal } from './AddDeviceModal';

const DeviceManagement: React.FC<DeviceManagementProps> = ({
  devices,
  onAddDevice,
  onRemoveDevice,
  onTrustDevice,
  onUntrustDevice,
  onUpdateDevice,
  onSelectDevice,
  onSelectAllDevices,
  selectedDevices,
  isLoading,
  showAddDeviceModal,
  onShowAddDeviceModal
}) => {
  const [filterType, setFilterType] = useState<'all' | 'trusted' | 'untrusted' | 'active' | 'inactive'>('all');
  const [filterDeviceType, setFilterDeviceType] = useState<'all' | 'mobile' | 'desktop' | 'tablet' | 'other'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'lastUsed' | 'trustScore' | 'createdAt' | 'usageCount'>('lastUsed');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const filteredAndSortedDevices = useMemo(() => {
    let filtered = devices.filter(device => {
      if (filterType !== 'all') {
        switch (filterType) {
          case 'trusted':
            if (!device.isTrusted) return false;
            break;
          case 'untrusted':
            if (device.isTrusted) return false;
            break;
          case 'active':
            if (!device.isActive) return false;
            break;
          case 'inactive':
            if (device.isActive) return false;
            break;
        }
      }

      if (filterDeviceType !== 'all' && device.type !== filterDeviceType) {
        return false;
      }

      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        return (
          device.name.toLowerCase().includes(searchLower) ||
          device.model?.toLowerCase().includes(searchLower) ||
          device.operatingSystem?.toLowerCase().includes(searchLower) ||
          device.browser?.toLowerCase().includes(searchLower) ||
          device.lastIpAddress.includes(searchTerm)
        );
      }

      return true;
    });

    // Sort devices
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'lastUsed':
          aValue = new Date(a.lastUsed).getTime();
          bValue = new Date(b.lastUsed).getTime();
          break;
        case 'trustScore':
          aValue = a.trustScore;
          bValue = b.trustScore;
          break;
        case 'createdAt':
          aValue = new Date(a.createdAt).getTime();
          bValue = new Date(b.createdAt).getTime();
          break;
        case 'usageCount':
          aValue = a.usageCount;
          bValue = b.usageCount;
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
  }, [devices, filterType, filterDeviceType, searchTerm, sortBy, sortOrder]);

  const handleSelectAll = (selected: boolean) => {
    onSelectAllDevices(selected);
  };

  const handleBulkTrust = async () => {
    for (const deviceId of selectedDevices) {
      await onTrustDevice(deviceId);
    }
  };

  const handleBulkUntrust = async () => {
    for (const deviceId of selectedDevices) {
      await onUntrustDevice(deviceId);
    }
  };

  const handleBulkRemove = async () => {
    for (const deviceId of selectedDevices) {
      await onRemoveDevice(deviceId);
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

  const getTrustLevelColor = (trustLevel: string) => {
    switch (trustLevel) {
      case 'verified': return 'text-green-600 bg-green-100';
      case 'trusted': return 'text-blue-600 bg-blue-100';
      case 'basic': return 'text-yellow-600 bg-yellow-100';
      case 'untrusted': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (isLoading) {
    return <LoadingSkeleton type="device" count={4} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Device Management</h2>
          <p className="text-gray-600 mt-1">
            Manage your trusted devices and monitor device security
          </p>
        </div>
        
        <div className="mt-4 sm:mt-0 flex items-center space-x-3">
          <button
            onClick={() => onShowAddDeviceModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Add Device
          </button>
        </div>
      </div>

      {/* Device Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Devices</p>
              <p className="text-2xl font-bold text-gray-900">{devices.length}</p>
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
              <p className="text-2xl font-bold text-gray-900">
                {devices.filter(d => d.isTrusted).length}
              </p>
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
              <p className="text-sm text-gray-500">Active</p>
              <p className="text-2xl font-bold text-gray-900">
                {devices.filter(d => d.isActive).length}
              </p>
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
              <p className="text-sm text-gray-500">Avg Trust Score</p>
              <p className="text-2xl font-bold text-gray-900">
                {Math.round(devices.reduce((sum, d) => sum + d.trustScore, 0) / devices.length || 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Filter by:</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as any)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Devices</option>
                <option value="trusted">Trusted</option>
                <option value="untrusted">Untrusted</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Type:</label>
              <select
                value={filterDeviceType}
                onChange={(e) => setFilterDeviceType(e.target.value as any)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                <option value="mobile">Mobile</option>
                <option value="desktop">Desktop</option>
                <option value="tablet">Tablet</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Search devices..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <svg className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Sort by:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="lastUsed">Last Used</option>
                <option value="trustScore">Trust Score</option>
                <option value="createdAt">Created</option>
                <option value="usageCount">Usage Count</option>
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
      {selectedDevices.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-blue-900">
                {selectedDevices.length} device{selectedDevices.length !== 1 ? 's' : ''} selected
              </span>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleBulkTrust}
                  className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
                >
                  Trust All
                </button>
                <button
                  onClick={handleBulkUntrust}
                  className="px-3 py-1 bg-yellow-600 text-white text-sm rounded-md hover:bg-yellow-700 transition-colors"
                >
                  Untrust All
                </button>
                <button
                  onClick={handleBulkRemove}
                  className="px-3 py-1 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
                >
                  Remove All
                </button>
              </div>
            </div>
            
            <button
              onClick={() => onSelectAllDevices(false)}
              className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
            >
              Clear Selection
            </button>
          </div>
        </div>
      )}

      {/* Devices List */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedDevices.length === filteredAndSortedDevices.length && filteredAndSortedDevices.length > 0}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Select All</span>
              </label>
              
              <span className="text-sm text-gray-500">
                {selectedDevices.length} of {filteredAndSortedDevices.length} selected
              </span>
            </div>
            
            <span className="text-sm text-gray-500">
              {filteredAndSortedDevices.length} devices
            </span>
          </div>
        </div>

        {filteredAndSortedDevices.length === 0 ? (
          <div className="p-8 text-center">
            <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No devices found</h3>
            <p className="text-gray-500">
              {searchTerm || filterType !== 'all' || filterDeviceType !== 'all'
                ? 'Try adjusting your filters or search terms'
                : 'No devices registered yet. Add your first device to get started.'}
            </p>
            {!searchTerm && filterType === 'all' && filterDeviceType === 'all' && (
              <button
                onClick={() => onShowAddDeviceModal(true)}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Add Device
              </button>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredAndSortedDevices.map((device) => (
              <DeviceCard
                key={device.id}
                device={device}
                isSelected={selectedDevices.includes(device.id)}
                onSelect={(selected) => onSelectDevice(device.id, selected)}
                onRemove={() => onRemoveDevice(device.id)}
                onTrust={() => onTrustDevice(device.id)}
                onUntrust={() => onUntrustDevice(device.id)}
                onUpdate={(updates) => onUpdateDevice(device.id, updates)}
                onViewDetails={() => {
                  // Handle view details - could open modal or navigate
                  console.log('View details for device:', device.id);
                }}
                showActions={true}
              />
            ))}
          </div>
        )}
      </div>

      {/* Add Device Modal */}
      {showAddDeviceModal && (
        <AddDeviceModal
          onClose={() => onShowAddDeviceModal(false)}
          onAddDevice={onAddDevice}
        />
      )}
    </div>
  );
};

export default DeviceManagement;
