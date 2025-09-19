// Vehicle Dashboard TypeScript Interfaces
// Comprehensive type definitions for vehicle management system

export interface Vehicle {
  id: number;
  vin: string;
  year: number;
  make: string;
  model: string;
  trim?: string;
  currentMileage: number;
  monthlyMiles: number;
  userZipcode: string;
  assignedMsa?: string;
  createdAt: string;
  updatedAt: string;
}

export interface VehicleStats {
  totalVehicles: number;
  totalMileage: number;
  averageMonthlyMiles: number;
  totalMonthlyBudget: number;
  upcomingMaintenanceCount: number;
  overdueMaintenanceCount: number;
}

export interface MaintenanceItem {
  id: number;
  vehicleId: number;
  type: 'oil_change' | 'tire_rotation' | 'brake_service' | 'transmission' | 'inspection' | 'other';
  description: string;
  dueDate: string;
  estimatedCost: number;
  mileageThreshold?: number;
  isOverdue: boolean;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'scheduled' | 'completed' | 'overdue' | 'cancelled';
  notes?: string;
}

export interface MaintenancePrediction {
  id: number;
  vehicleId: number;
  maintenanceType: string;
  predictedDate: string;
  confidence: number;
  estimatedCost: number;
  mileageAtService: number;
  factors: string[];
}

export interface VehicleBudget {
  vehicleId: number;
  monthlyBudget: number;
  fuelBudget: number;
  maintenanceBudget: number;
  insuranceBudget: number;
  totalSpent: number;
  remainingBudget: number;
  budgetPeriod: string; // e.g., "2024-01"
}

export interface VehicleExpense {
  id: number;
  vehicleId: number;
  type: 'fuel' | 'maintenance' | 'insurance' | 'registration' | 'repair' | 'other';
  amount: number;
  description: string;
  date: string;
  category: string;
  receiptUrl?: string;
}

export interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'red' | 'gray';
  enabled: boolean;
  href?: string;
  onClick?: () => void;
}

export interface VehicleDashboardData {
  vehicles: Vehicle[];
  stats: VehicleStats;
  upcomingMaintenance: MaintenanceItem[];
  maintenancePredictions: MaintenancePrediction[];
  budgets: VehicleBudget[];
  recentExpenses: VehicleExpense[];
  quickActions: QuickAction[];
}

export interface VehicleDashboardState {
  loading: boolean;
  error: string | null;
  lastUpdated: string;
  refreshInterval: number;
  autoRefresh: boolean;
}
