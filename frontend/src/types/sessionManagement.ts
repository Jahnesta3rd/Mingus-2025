export interface Session {
  id: string;
  userId: string;
  deviceId: string;
  deviceName: string;
  deviceType: 'mobile' | 'desktop' | 'tablet' | 'other';
  deviceModel?: string;
  browser?: string;
  browserVersion?: string;
  operatingSystem?: string;
  osVersion?: string;
  ipAddress: string;
  location: SessionLocation;
  userAgent: string;
  isActive: boolean;
  isTrusted: boolean;
  isCurrentSession: boolean;
  lastActivity: string;
  createdAt: string;
  expiresAt: string;
  sessionDuration: number; // in minutes
  activityCount: number;
  lastActivityType: 'login' | 'logout' | 'action' | 'timeout' | 'manual_termination';
  securityScore: number; // 0-100
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  flags: SessionFlag[];
  metadata: Record<string, any>;
}

export interface SessionLocation {
  country: string;
  region: string;
  city: string;
  latitude: number;
  longitude: number;
  timezone: string;
  isp: string;
  isVpn: boolean;
  isProxy: boolean;
  isTor: boolean;
  riskScore: number; // 0-100
}

export interface SessionFlag {
  type: 'suspicious_ip' | 'unusual_location' | 'multiple_sessions' | 'vpn_detected' | 'tor_detected' | 'unusual_time' | 'device_mismatch' | 'behavior_anomaly';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  timestamp: string;
  isResolved: boolean;
  resolutionNote?: string;
}

export interface Device {
  id: string;
  userId: string;
  name: string;
  type: 'mobile' | 'desktop' | 'tablet' | 'other';
  model?: string;
  manufacturer?: string;
  operatingSystem?: string;
  osVersion?: string;
  browser?: string;
  browserVersion?: string;
  fingerprint: string; // Device fingerprint hash
  isTrusted: boolean;
  isActive: boolean;
  trustLevel: 'untrusted' | 'basic' | 'trusted' | 'verified';
  trustScore: number; // 0-100
  lastUsed: string;
  createdAt: string;
  lastIpAddress: string;
  lastLocation: SessionLocation;
  usageCount: number;
  securityEvents: SecurityEvent[];
  metadata: Record<string, any>;
}

export interface SecurityEvent {
  id: string;
  type: 'login_attempt' | 'failed_login' | 'suspicious_activity' | 'location_change' | 'device_change' | 'password_change' | '2fa_enabled' | '2fa_disabled' | 'session_created' | 'session_terminated';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  timestamp: string;
  ipAddress?: string;
  location?: SessionLocation;
  deviceId?: string;
  sessionId?: string;
  isResolved: boolean;
  resolutionNote?: string;
  metadata: Record<string, any>;
}

export interface SessionSettings {
  maxConcurrentSessions: number;
  sessionTimeoutMinutes: number;
  idleTimeoutMinutes: number;
  requireReauthForSensitiveActions: boolean;
  enableLocationTracking: boolean;
  enableDeviceFingerprinting: boolean;
  enableBehavioralAnalysis: boolean;
  enableVpnDetection: boolean;
  enableTorDetection: boolean;
  enableSuspiciousActivityAlerts: boolean;
  enableSessionHistory: boolean;
  maxSessionHistoryDays: number;
  trustedDeviceExpiryDays: number;
  securityScoreThreshold: number;
  autoTerminateSuspiciousSessions: boolean;
  notificationPreferences: NotificationPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  sms: boolean;
  inApp: boolean;
  suspiciousActivity: boolean;
  newDeviceLogin: boolean;
  locationChange: boolean;
  sessionTimeout: boolean;
  securityScoreChange: boolean;
}

export interface SessionAlert {
  id: string;
  type: 'suspicious_activity' | 'new_device' | 'location_change' | 'security_threat' | 'session_timeout' | 'device_compromise' | 'account_lockout' | 'unusual_behavior';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  description: string;
  timestamp: string;
  isRead: boolean;
  isResolved: boolean;
  requiresAction: boolean;
  actionRequired: 'none' | 'verify_device' | 'change_password' | 'enable_2fa' | 'contact_support' | 'review_activity';
  affectedSessions: string[];
  affectedDevices: string[];
  location?: SessionLocation;
  ipAddress?: string;
  deviceId?: string;
  sessionId?: string;
  metadata: Record<string, any>;
}

export interface SecurityDashboard {
  overallSecurityScore: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  activeSessions: number;
  trustedDevices: number;
  suspiciousActivities: number;
  securityEvents: SecurityEvent[];
  recentAlerts: SessionAlert[];
  locationAnomalies: number;
  deviceAnomalies: number;
  lastSecurityReview: string;
  nextSecurityReview: string;
  recommendations: SecurityRecommendation[];
  trends: SecurityTrend[];
}

export interface SecurityRecommendation {
  id: string;
  type: 'enable_2fa' | 'review_devices' | 'change_password' | 'enable_location_tracking' | 'review_sessions' | 'update_security_settings' | 'contact_support';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  impact: string;
  effort: 'low' | 'medium' | 'high';
  isImplemented: boolean;
  implementedAt?: string;
  metadata: Record<string, any>;
}

export interface SecurityTrend {
  date: string;
  securityScore: number;
  activeSessions: number;
  securityEvents: number;
  suspiciousActivities: number;
  locationAnomalies: number;
  deviceAnomalies: number;
}

export interface SessionFilter {
  deviceType?: 'mobile' | 'desktop' | 'tablet' | 'other';
  riskLevel?: 'low' | 'medium' | 'high' | 'critical';
  location?: string;
  isTrusted?: boolean;
  isActive?: boolean;
  dateRange?: {
    start: string;
    end: string;
  };
  searchTerm?: string;
}

export interface SessionStats {
  totalSessions: number;
  activeSessions: number;
  trustedSessions: number;
  suspiciousSessions: number;
  terminatedSessions: number;
  averageSessionDuration: number;
  sessionsByDeviceType: Record<string, number>;
  sessionsByLocation: Record<string, number>;
  sessionsByRiskLevel: Record<string, number>;
}

export interface SessionAction {
  type: 'terminate' | 'trust' | 'untrust' | 'investigate' | 'block_ip' | 'allow_ip' | 'flag_suspicious' | 'resolve_flag';
  sessionId: string;
  deviceId?: string;
  ipAddress?: string;
  reason?: string;
  metadata?: Record<string, any>;
}

export interface WebSocketMessage {
  type: 'session_update' | 'session_created' | 'session_terminated' | 'security_alert' | 'device_update' | 'location_change' | 'activity_log';
  payload: any;
  timestamp: string;
  userId: string;
}

export interface SessionManagementState {
  sessions: Session[];
  devices: Device[];
  alerts: SessionAlert[];
  settings: SessionSettings;
  dashboard: SecurityDashboard;
  stats: SessionStats;
  isLoading: boolean;
  error: string | null;
  lastSync: string;
  isOffline: boolean;
  filters: SessionFilter;
  selectedSessions: string[];
  selectedDevices: string[];
}

export interface SessionManagementActions {
  // Session management
  getSessions: (filters?: SessionFilter) => Promise<Session[]>;
  terminateSession: (sessionId: string, reason?: string) => Promise<void>;
  terminateMultipleSessions: (sessionIds: string[], reason?: string) => Promise<void>;
  trustSession: (sessionId: string) => Promise<void>;
  untrustSession: (sessionId: string) => Promise<void>;
  
  // Device management
  getDevices: () => Promise<Device[]>;
  addDevice: (device: Omit<Device, 'id' | 'userId' | 'createdAt' | 'lastUsed' | 'usageCount' | 'securityEvents'>) => Promise<Device>;
  removeDevice: (deviceId: string) => Promise<void>;
  trustDevice: (deviceId: string) => Promise<void>;
  untrustDevice: (deviceId: string) => Promise<void>;
  updateDevice: (deviceId: string, updates: Partial<Device>) => Promise<Device>;
  
  // Alert management
  getAlerts: () => Promise<SessionAlert[]>;
  markAlertAsRead: (alertId: string) => Promise<void>;
  resolveAlert: (alertId: string, resolutionNote?: string) => Promise<void>;
  dismissAlert: (alertId: string) => Promise<void>;
  
  // Settings management
  getSettings: () => Promise<SessionSettings>;
  updateSettings: (updates: Partial<SessionSettings>) => Promise<SessionSettings>;
  
  // Dashboard and stats
  getDashboard: () => Promise<SecurityDashboard>;
  getStats: (filters?: SessionFilter) => Promise<SessionStats>;
  
  // Security actions
  blockIP: (ipAddress: string, reason?: string) => Promise<void>;
  allowIP: (ipAddress: string) => Promise<void>;
  flagSuspiciousActivity: (sessionId: string, reason: string) => Promise<void>;
  
  // Real-time updates
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  
  // Utility actions
  refreshData: () => Promise<void>;
  clearFilters: () => void;
  updateFilters: (filters: Partial<SessionFilter>) => void;
  selectSessions: (sessionIds: string[]) => void;
  selectDevices: (deviceIds: string[]) => void;
  clearSelection: () => void;
}

export interface SessionManagementContextValue extends SessionManagementState, SessionManagementActions {}

// Component-specific props interfaces
export interface ActiveSessionsProps {
  sessions: Session[];
  onTerminateSession: (sessionId: string, reason?: string) => Promise<void>;
  onTerminateMultipleSessions: (sessionIds: string[], reason?: string) => Promise<void>;
  onTrustSession: (sessionId: string) => Promise<void>;
  onUntrustSession: (sessionId: string) => Promise<void>;
  onSelectSession: (sessionId: string, selected: boolean) => void;
  onSelectAllSessions: (selected: boolean) => void;
  selectedSessions: string[];
  isLoading: boolean;
  filters: SessionFilter;
  onUpdateFilters: (filters: Partial<SessionFilter>) => void;
  stats: SessionStats;
}

export interface SessionAlertProps {
  alerts: SessionAlert[];
  onMarkAsRead: (alertId: string) => Promise<void>;
  onResolve: (alertId: string, resolutionNote?: string) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
  onTakeAction: (alert: SessionAlert) => void;
  isLoading: boolean;
  unreadCount: number;
}

export interface SessionSettingsProps {
  settings: SessionSettings;
  onUpdateSettings: (updates: Partial<SessionSettings>) => Promise<void>;
  onResetToDefaults: () => Promise<void>;
  isLoading: boolean;
  hasChanges: boolean;
}

export interface DeviceManagementProps {
  devices: Device[];
  onAddDevice: (device: Omit<Device, 'id' | 'userId' | 'createdAt' | 'lastUsed' | 'usageCount' | 'securityEvents'>) => Promise<Device>;
  onRemoveDevice: (deviceId: string) => Promise<void>;
  onTrustDevice: (deviceId: string) => Promise<void>;
  onUntrustDevice: (deviceId: string) => Promise<void>;
  onUpdateDevice: (deviceId: string, updates: Partial<Device>) => Promise<Device>;
  onSelectDevice: (deviceId: string, selected: boolean) => void;
  onSelectAllDevices: (selected: boolean) => void;
  selectedDevices: string[];
  isLoading: boolean;
  showAddDeviceModal: boolean;
  onShowAddDeviceModal: (show: boolean) => void;
}

export interface SecurityDashboardProps {
  dashboard: SecurityDashboard;
  stats: SessionStats;
  recentAlerts: SessionAlert[];
  onRefresh: () => Promise<void>;
  onViewDetails: (type: 'sessions' | 'devices' | 'alerts' | 'events') => void;
  isLoading: boolean;
  lastUpdated: string;
}

export interface SessionCardProps {
  session: Session;
  isSelected: boolean;
  onSelect: (selected: boolean) => void;
  onTerminate: (reason?: string) => Promise<void>;
  onTrust: () => Promise<void>;
  onUntrust: () => Promise<void>;
  onViewDetails: () => void;
  showActions: boolean;
}

export interface DeviceCardProps {
  device: Device;
  isSelected: boolean;
  onSelect: (selected: boolean) => void;
  onRemove: () => Promise<void>;
  onTrust: () => Promise<void>;
  onUntrust: () => Promise<void>;
  onUpdate: (updates: Partial<Device>) => Promise<void>;
  onViewDetails: () => void;
  showActions: boolean;
}

export interface AlertCardProps {
  alert: SessionAlert;
  onMarkAsRead: () => Promise<void>;
  onResolve: (resolutionNote?: string) => Promise<void>;
  onDismiss: () => Promise<void>;
  onTakeAction: () => void;
  onViewDetails: () => void;
}

export interface LocationMapProps {
  sessions: Session[];
  onSessionClick: (session: Session) => void;
  centerLocation?: { lat: number; lng: number };
  zoom?: number;
  height?: string;
}

export interface SecurityScoreGaugeProps {
  score: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
  animated?: boolean;
}

export interface ActivityTimelineProps {
  events: SecurityEvent[];
  onEventClick: (event: SecurityEvent) => void;
  maxEvents?: number;
  showFilters?: boolean;
}

export interface FilterPanelProps {
  filters: SessionFilter;
  onUpdateFilters: (filters: Partial<SessionFilter>) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
  stats: SessionStats;
  isLoading: boolean;
}

export interface BulkActionsProps {
  selectedSessions: string[];
  selectedDevices: string[];
  onTerminateSessions: (reason?: string) => Promise<void>;
  onTrustSessions: () => Promise<void>;
  onUntrustSessions: () => Promise<void>;
  onRemoveDevices: () => Promise<void>;
  onTrustDevices: () => Promise<void>;
  onUntrustDevices: () => Promise<void>;
  isLoading: boolean;
}

export interface OfflineIndicatorProps {
  isOffline: boolean;
  lastSync: string;
  onRetry: () => void;
  onManualSync: () => void;
}

export interface LoadingSkeletonProps {
  type: 'session' | 'device' | 'alert' | 'dashboard' | 'table';
  count?: number;
  height?: string;
}

export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}
