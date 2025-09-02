export interface TwoFactorSetup {
  secret: string;
  qrCodeUrl: string;
  backupCodes: string[];
  isEnabled: boolean;
  setupComplete: boolean;
}

export interface TwoFactorVerification {
  code: string;
  method: 'totp' | 'sms' | 'backup';
  isVerified: boolean;
  attempts: number;
  maxAttempts: number;
}

export interface TwoFactorSettings {
  isEnabled: boolean;
  totpEnabled: boolean;
  smsEnabled: boolean;
  backupCodesEnabled: boolean;
  lastUpdated: string;
  devices: TwoFactorDevice[];
}

export interface TwoFactorDevice {
  id: string;
  name: string;
  type: 'mobile' | 'desktop' | 'tablet' | 'other';
  lastUsed: string;
  isTrusted: boolean;
  ipAddress?: string;
  userAgent?: string;
}

export interface TwoFactorRecovery {
  backupCodes: string[];
  usedCodes: string[];
  remainingCodes: number;
  canGenerateNew: boolean;
  lastGenerated: string;
}

export interface TwoFactorState {
  setup: TwoFactorSetup;
  verification: TwoFactorVerification;
  settings: TwoFactorSettings;
  recovery: TwoFactorRecovery;
  isLoading: boolean;
  error: string | null;
  success: string | null;
}

export interface TwoFactorActions {
  enableTwoFactor: () => Promise<void>;
  disableTwoFactor: () => Promise<void>;
  verifyCode: (code: string, method?: 'totp' | 'sms' | 'backup') => Promise<boolean>;
  generateBackupCodes: () => Promise<string[]>;
  regenerateBackupCodes: () => Promise<string[]>;
  addDevice: (device: Omit<TwoFactorDevice, 'id' | 'lastUsed'>) => Promise<void>;
  removeDevice: (deviceId: string) => Promise<void>;
  updateSettings: (settings: Partial<TwoFactorSettings>) => Promise<void>;
  resetState: () => void;
}

export interface TwoFactorContextValue extends TwoFactorState, TwoFactorActions {}

export interface QRCodeScannerProps {
  onScan: (result: string) => void;
  onError: (error: string) => void;
  onClose: () => void;
}

export interface TOTPInputProps {
  length: number;
  value: string;
  onChange: (value: string) => void;
  onComplete: (value: string) => void;
  error?: string;
  disabled?: boolean;
  autoFocus?: boolean;
}

export interface BackupCodeDisplayProps {
  codes: string[];
  onCopy: (code: string) => void;
  onDownload: () => void;
  onPrint: () => void;
  showRegenerate?: boolean;
  onRegenerate?: () => void;
}

export interface DeviceManagementProps {
  devices: TwoFactorDevice[];
  onAddDevice: (device: Omit<TwoFactorDevice, 'id' | 'lastUsed'>) => Promise<void>;
  onRemoveDevice: (deviceId: string) => Promise<void>;
  onTrustDevice: (deviceId: string) => Promise<void>;
}

export interface TwoFactorSetupStep {
  id: string;
  title: string;
  description: string;
  isComplete: boolean;
  isActive: boolean;
  component: React.ComponentType<any>;
}

export interface TwoFactorSetupFlow {
  currentStep: number;
  steps: TwoFactorSetupStep[];
  onNext: () => void;
  onPrevious: () => void;
  onComplete: () => void;
  canProceed: boolean;
}

export interface BiometricAuthProps {
  isAvailable: boolean;
  isEnabled: boolean;
  onEnable: () => Promise<void>;
  onDisable: () => Promise<void>;
  onAuthenticate: () => Promise<boolean>;
}

export interface OfflineIndicatorProps {
  isOffline: boolean;
  lastSync: string;
  onRetry: () => void;
}

export interface ProgressIndicatorProps {
  current: number;
  total: number;
  steps: string[];
  onStepClick?: (stepIndex: number) => void;
  showLabels?: boolean;
}

export interface ErrorDisplayProps {
  error: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  showDetails?: boolean;
}

export interface SuccessDisplayProps {
  message: string;
  onContinue?: () => void;
  onDismiss?: () => void;
  showAnimation?: boolean;
}
