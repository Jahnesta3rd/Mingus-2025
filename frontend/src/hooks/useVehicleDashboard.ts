import { useCallback, useEffect, useState } from 'react';
import type { MaintenanceItem, Vehicle, VehicleDashboardData, VehicleStats } from '../types/vehicle';

export interface VehicleSummary {
  totalVehicles: number;
  totalMonthlyBudget: number;
  upcomingMaintenanceCount: number;
  overdueMaintenanceCount: number;
  primaryVehicle: {
    year: number;
    make: string;
    model: string;
    currentMileage: number;
    monthlyMiles: number;
  } | null;
  nextMaintenance: {
    description: string;
    dueDate: string;
    estimatedCost: number;
    isOverdue: boolean;
  } | null;
  hasVehicles: boolean;
}

export interface UseVehicleDashboardResult {
  data: VehicleSummary | null;
  loading: boolean;
  error: boolean;
  refetch: () => void;
}

function buildAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': token || 'test-token',
  };
  if (token) {
    (headers as Record<string, string>).Authorization = `Bearer ${token}`;
  }
  return headers;
}

function summarizeDashboard(payload: VehicleDashboardData): VehicleSummary {
  const stats: VehicleStats = payload.stats ?? {
    totalVehicles: 0,
    totalMileage: 0,
    averageMonthlyMiles: 0,
    totalMonthlyBudget: 0,
    upcomingMaintenanceCount: 0,
    overdueMaintenanceCount: 0,
  };
  const vehicles: Vehicle[] = payload.vehicles ?? [];
  const upcoming: MaintenanceItem[] = payload.upcomingMaintenance ?? [];

  const primary = vehicles[0] ?? null;
  const next = upcoming[0] ?? null;

  return {
    totalVehicles: stats.totalVehicles,
    totalMonthlyBudget: stats.totalMonthlyBudget,
    upcomingMaintenanceCount: stats.upcomingMaintenanceCount,
    overdueMaintenanceCount: stats.overdueMaintenanceCount,
    primaryVehicle: primary
      ? {
          year: primary.year,
          make: primary.make,
          model: primary.model,
          currentMileage: primary.currentMileage,
          monthlyMiles: primary.monthlyMiles,
        }
      : null,
    nextMaintenance: next
      ? {
          description: next.description,
          dueDate: next.dueDate,
          estimatedCost: next.estimatedCost,
          isOverdue: next.isOverdue,
        }
      : null,
    hasVehicles: vehicles.length > 0,
  };
}

async function fetchVehicleDashboard(): Promise<VehicleSummary> {
  const res = await fetch('/api/vehicles/dashboard', {
    credentials: 'include',
    headers: buildAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error('Failed to load vehicle dashboard');
  }
  const json = (await res.json()) as VehicleDashboardData;
  return summarizeDashboard(json);
}

export function useVehicleDashboard(): UseVehicleDashboardResult {
  const [data, setData] = useState<VehicleSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [fetchKey, setFetchKey] = useState(0);

  const refetch = useCallback(() => {
    setFetchKey((k) => k + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);

    fetchVehicleDashboard()
      .then((summary) => {
        if (cancelled) return;
        setData(summary);
        setError(false);
      })
      .catch(() => {
        if (cancelled) return;
        setData(null);
        setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [fetchKey]);

  return { data, loading, error, refetch };
}
