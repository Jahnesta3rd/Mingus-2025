import React from 'react';

const DashboardSkeleton: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Skeleton */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="hidden sm:block">
                <div className="h-4 w-40 bg-gray-200 rounded animate-pulse" />
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
              <div className="h-6 w-20 bg-gray-200 rounded-full animate-pulse" />
            </div>
          </div>
        </div>
      </div>
      
      {/* Main Content Skeleton */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          
          {/* Risk Status Hero Skeleton */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-300 to-gray-400 p-6 shadow-xl animate-pulse">
            <div className="absolute inset-0 bg-black/10 backdrop-blur-sm" />
            
            <div className="relative z-10 flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className="h-8 w-8 bg-white/30 rounded" />
                  <div>
                    <div className="h-5 w-32 bg-white/30 rounded mb-2" />
                    <div className="h-4 w-24 bg-white/20 rounded" />
                  </div>
                </div>
                
                <div className="h-4 w-full bg-white/30 rounded mb-2" />
                <div className="h-4 w-3/4 bg-white/20 rounded mb-4" />
                
                <div className="h-4 w-48 bg-white/30 rounded mb-2" />
                <div className="h-3 w-32 bg-white/20 rounded mb-4" />
                
                <div className="h-12 w-48 bg-white/30 rounded" />
              </div>
              
              <div className="flex-shrink-0 ml-6">
                <div className="w-24 h-24 bg-white/30 rounded-full" />
              </div>
            </div>
          </div>
          
          {/* Tab Navigation Skeleton */}
          <div className="border-b border-gray-200">
            <div className="-mb-px flex space-x-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="py-2 px-1">
                  <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
                </div>
              ))}
            </div>
          </div>
          
          {/* Content Skeleton */}
          <div className="min-h-[600px]">
            <div className="grid gap-8 lg:grid-cols-2">
              <div>
                <div className="h-6 w-32 bg-gray-200 rounded animate-pulse mb-4" />
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-white border border-gray-200 rounded-lg p-4">
                      <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse mb-2" />
                      <div className="h-3 w-1/2 bg-gray-200 rounded animate-pulse" />
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <div className="h-6 w-32 bg-gray-200 rounded animate-pulse mb-4" />
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-white border border-gray-200 rounded-lg p-4">
                      <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse mb-2" />
                      <div className="h-3 w-1/2 bg-gray-200 rounded animate-pulse" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
};

export default DashboardSkeleton;
