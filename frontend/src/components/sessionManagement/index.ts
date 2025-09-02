// Main Components
export { default as ActiveSessions } from './ActiveSessions';
export { default as SessionAlert } from './SessionAlert';
export { default as SessionSettings } from './SessionSettings';
export { default as DeviceManagement } from './DeviceManagement';
export { default as SecurityDashboard } from './SecurityDashboard';

// Supporting Components (to be created)
export { default as SessionCard } from './SessionCard';
export { default as DeviceCard } from './DeviceCard';
export { default as AlertCard } from './AlertCard';
export { default as FilterPanel } from './FilterPanel';
export { default as BulkActions } from './BulkActions';
export { default as LoadingSkeleton } from './LoadingSkeleton';
export { default as OfflineIndicator } from './OfflineIndicator';
export { default as LocationMap } from './LocationMap';
export { default as SecurityScoreGauge } from './SecurityScoreGauge';
export { default as ActivityTimeline } from './ActivityTimeline';
export { default as AddDeviceModal } from './AddDeviceModal';

// Types
export type {
  // Core interfaces
  Session,
  SessionLocation,
  SessionFlag,
  Device,
  SecurityEvent,
  SessionSettings,
  NotificationPreferences,
  SessionAlert,
  SecurityDashboard,
  SecurityRecommendation,
  SecurityTrend,
  SessionFilter,
  SessionStats,
  SessionAction,
  WebSocketMessage,
  
  // State and actions
  SessionManagementState,
  SessionManagementActions,
  SessionManagementContextValue,
  
  // Component props
  ActiveSessionsProps,
  SessionAlertProps,
  SessionSettingsProps,
  DeviceManagementProps,
  SecurityDashboardProps,
  SessionCardProps,
  DeviceCardProps,
  AlertCardProps,
  LocationMapProps,
  SecurityScoreGaugeProps,
  ActivityTimelineProps,
  FilterPanelProps,
  BulkActionsProps,
  OfflineIndicatorProps,
  LoadingSkeletonProps,
  ErrorBoundaryProps,
  ErrorBoundaryState
} from '@/types/sessionManagement';
