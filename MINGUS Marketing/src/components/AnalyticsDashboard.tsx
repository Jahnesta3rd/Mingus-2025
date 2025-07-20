import React, { useState, useEffect } from 'react'
import { FunnelStage } from '../services/analytics'

// Analytics data interfaces
interface FunnelData {
  stage: FunnelStage
  count: number
  conversionRate: number
  dropoffRate: number
}

interface UserBehaviorData {
  action: string
  count: number
  percentage: number
  trend: 'up' | 'down' | 'stable'
}

interface ABTestData {
  testId: string
  name: string
  variants: {
    name: string
    impressions: number
    conversions: number
    conversionRate: number
    statisticalSignificance: boolean
  }[]
  winner?: string
  totalImpressions: number
  totalConversions: number
}

interface DeviceData {
  deviceType: string
  count: number
  percentage: number
  conversionRate: number
}

interface TrafficSourceData {
  source: string
  sessions: number
  conversions: number
  conversionRate: number
  averageSessionDuration: number
}

// Analytics Dashboard Component
export const AnalyticsDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'funnel' | 'behavior' | 'ab-tests' | 'devices' | 'traffic'>('funnel')
  const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d'>('30d')
  const [isLoading, setIsLoading] = useState(false)

  // Mock data - replace with real API calls
  const [funnelData, setFunnelData] = useState<FunnelData[]>([
    { stage: FunnelStage.LANDING_PAGE_VIEW, count: 1000, conversionRate: 100, dropoffRate: 0 },
    { stage: FunnelStage.QUESTIONNAIRE_START, count: 750, conversionRate: 75, dropoffRate: 25 },
    { stage: FunnelStage.QUESTION_COMPLETED, count: 600, conversionRate: 60, dropoffRate: 15 },
    { stage: FunnelStage.EMAIL_SUBMITTED, count: 450, conversionRate: 45, dropoffRate: 15 },
    { stage: FunnelStage.RESULTS_VIEWED, count: 400, conversionRate: 40, dropoffRate: 5 },
    { stage: FunnelStage.CTA_CLICKED, count: 120, conversionRate: 12, dropoffRate: 28 }
  ])

  const [behaviorData, setBehaviorData] = useState<UserBehaviorData[]>([
    { action: 'Questionnaire Start', count: 750, percentage: 75, trend: 'up' },
    { action: 'Question Completion', count: 600, percentage: 60, trend: 'up' },
    { action: 'Email Submission', count: 450, percentage: 45, trend: 'stable' },
    { action: 'Results View', count: 400, percentage: 40, trend: 'down' },
    { action: 'CTA Click', count: 120, percentage: 12, trend: 'up' }
  ])

  const [abTestData, setAbTestData] = useState<ABTestData[]>([
    {
      testId: 'headline_test',
      name: 'Landing Page Headlines',
      variants: [
        { name: 'Control', impressions: 300, conversions: 45, conversionRate: 15, statisticalSignificance: false },
        { name: 'Variant A', impressions: 300, conversions: 52, conversionRate: 17.3, statisticalSignificance: true },
        { name: 'Variant B', impressions: 400, conversions: 68, conversionRate: 17, statisticalSignificance: true }
      ],
      winner: 'Variant A',
      totalImpressions: 1000,
      totalConversions: 165
    }
  ])

  const [deviceData, setDeviceData] = useState<DeviceData[]>([
    { deviceType: 'Desktop', count: 600, percentage: 60, conversionRate: 18 },
    { deviceType: 'Mobile', count: 300, percentage: 30, conversionRate: 12 },
    { deviceType: 'Tablet', count: 100, percentage: 10, conversionRate: 15 }
  ])

  const [trafficData, setTrafficData] = useState<TrafficSourceData[]>([
    { source: 'Direct', sessions: 400, conversions: 60, conversionRate: 15, averageSessionDuration: 180 },
    { source: 'Organic Search', sessions: 300, conversions: 45, conversionRate: 15, averageSessionDuration: 240 },
    { source: 'Social Media', sessions: 200, conversions: 25, conversionRate: 12.5, averageSessionDuration: 120 },
    { source: 'Email', sessions: 100, conversions: 20, conversionRate: 20, averageSessionDuration: 300 }
  ])

  // Load analytics data
  useEffect(() => {
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false)
    }, 1000)
  }, [dateRange])

  // Funnel Chart Component
  const FunnelChart: React.FC<{ data: FunnelData[] }> = ({ data }) => (
    <div className="funnel-chart">
      {data.map((stage, index) => (
        <div key={stage.stage} className="funnel-stage mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold text-gray-700">
              {stage.stage.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
            <span className="text-sm text-gray-500">
              {stage.count.toLocaleString()} users ({stage.conversionRate}%)
            </span>
          </div>
          <div className="relative">
            <div 
              className="bg-blue-500 h-8 rounded-lg transition-all duration-500"
              style={{ width: `${stage.conversionRate}%` }}
            />
            {index < data.length - 1 && (
              <div className="text-xs text-gray-400 mt-1">
                Dropoff: {stage.dropoffRate}% ({stage.count - data[index + 1].count} users)
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )

  // Behavior Chart Component
  const BehaviorChart: React.FC<{ data: UserBehaviorData[] }> = ({ data }) => (
    <div className="behavior-chart">
      {data.map((item) => (
        <div key={item.action} className="behavior-item flex items-center justify-between p-4 bg-white rounded-lg shadow mb-3">
          <div className="flex items-center">
            <span className="font-medium text-gray-700">{item.action}</span>
            <span className={`ml-2 text-sm ${
              item.trend === 'up' ? 'text-green-500' : 
              item.trend === 'down' ? 'text-red-500' : 'text-gray-500'
            }`}>
              {item.trend === 'up' ? '↗' : item.trend === 'down' ? '↘' : '→'}
            </span>
          </div>
          <div className="text-right">
            <div className="font-semibold text-gray-900">{item.count.toLocaleString()}</div>
            <div className="text-sm text-gray-500">{item.percentage}%</div>
          </div>
        </div>
      ))}
    </div>
  )

  // A/B Test Results Component
  const ABTestResults: React.FC<{ data: ABTestData[] }> = ({ data }) => (
    <div className="ab-test-results">
      {data.map((test) => (
        <div key={test.testId} className="ab-test-item bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">{test.name}</h3>
            {test.winner && (
              <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                Winner: {test.winner}
              </span>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {test.variants.map((variant) => (
              <div
                key={variant.name}
                className={`p-4 rounded-lg border-2 ${
                  variant.name === test.winner ? 'border-green-500 bg-green-50' : 'border-gray-200'
                }`}
              >
                <div className="font-semibold text-lg mb-2">
                  {variant.name}
                  {variant.statisticalSignificance && (
                    <span className="ml-2 text-green-600">★</span>
                  )}
                </div>
                <div className="text-2xl font-bold text-blue-600">
                  {variant.conversionRate.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">
                  {variant.conversions} / {variant.impressions} conversions
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-4 text-sm text-gray-500">
            Total: {test.totalImpressions.toLocaleString()} impressions, {test.totalConversions.toLocaleString()} conversions
          </div>
        </div>
      ))}
    </div>
  )

  // Device Chart Component
  const DeviceChart: React.FC<{ data: DeviceData[] }> = ({ data }) => (
    <div className="device-chart">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data.map((device) => (
          <div key={device.deviceType} className="device-item bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-gray-700">{device.deviceType}</span>
              <span className="text-sm text-gray-500">{device.percentage}%</span>
            </div>
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {device.count.toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">
              {device.conversionRate}% conversion rate
            </div>
          </div>
        ))}
      </div>
    </div>
  )

  // Traffic Chart Component
  const TrafficChart: React.FC<{ data: TrafficSourceData[] }> = ({ data }) => (
    <div className="traffic-chart">
      {data.map((source) => (
        <div key={source.source} className="traffic-item flex items-center justify-between p-4 bg-white rounded-lg shadow mb-3">
          <div>
            <div className="font-semibold text-gray-900">{source.source}</div>
            <div className="text-sm text-gray-500">
              {source.sessions.toLocaleString()} sessions
            </div>
          </div>
          <div className="text-right">
            <div className="font-semibold text-blue-600">
              {source.conversionRate.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500">
              {source.conversions.toLocaleString()} conversions
            </div>
            <div className="text-xs text-gray-400">
              {Math.round(source.averageSessionDuration / 60)}m avg session
            </div>
          </div>
        </div>
      ))}
    </div>
  )

  return (
    <div className="analytics-dashboard bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics Dashboard</h1>
          <p className="text-gray-600">Track your lead magnet performance and user behavior</p>
        </div>

        {/* Controls */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
          {/* Date Range Selector */}
          <div className="flex space-x-2 mb-4 sm:mb-0">
            {(['7d', '30d', '90d'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setDateRange(range)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  dateRange === range
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : '90 Days'}
              </button>
            ))}
          </div>

          {/* Refresh Button */}
          <button
            onClick={() => setIsLoading(true)}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? 'Loading...' : 'Refresh Data'}
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'funnel', label: 'Conversion Funnel' },
              { id: 'behavior', label: 'User Behavior' },
              { id: 'ab-tests', label: 'A/B Tests' },
              { id: 'devices', label: 'Devices' },
              { id: 'traffic', label: 'Traffic Sources' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="p-6">
              {activeTab === 'funnel' && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Conversion Funnel</h2>
                  <FunnelChart data={funnelData} />
                </div>
              )}

              {activeTab === 'behavior' && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">User Behavior</h2>
                  <BehaviorChart data={behaviorData} />
                </div>
              )}

              {activeTab === 'ab-tests' && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">A/B Test Results</h2>
                  <ABTestResults data={abTestData} />
                </div>
              )}

              {activeTab === 'devices' && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Device Performance</h2>
                  <DeviceChart data={deviceData} />
                </div>
              )}

              {activeTab === 'traffic' && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Traffic Sources</h2>
                  <TrafficChart data={trafficData} />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Summary Stats */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500">Total Sessions</div>
            <div className="text-2xl font-bold text-gray-900">1,234</div>
            <div className="text-sm text-green-600">+12% from last period</div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500">Conversion Rate</div>
            <div className="text-2xl font-bold text-gray-900">12.3%</div>
            <div className="text-sm text-green-600">+2.1% from last period</div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500">Avg Session Duration</div>
            <div className="text-2xl font-bold text-gray-900">3m 24s</div>
            <div className="text-sm text-red-600">-0.5m from last period</div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500">Bounce Rate</div>
            <div className="text-2xl font-bold text-gray-900">34.2%</div>
            <div className="text-sm text-green-600">-5.1% from last period</div>
          </div>
        </div>
      </div>
    </div>
  )
} 