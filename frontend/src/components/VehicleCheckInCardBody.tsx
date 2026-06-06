import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useVehicleDashboard } from '../hooks/useVehicleDashboard';

export interface VehicleCheckInCardBodyProps {
  userEmail: string;
  userTier: 'budget' | 'mid_tier' | 'professional';
}

const labelStyle: React.CSSProperties = {
  fontSize: 9,
  color: '#7dd3fc',
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  margin: 0,
  fontWeight: 600,
};

const dividerStyle: React.CSSProperties = {
  height: 1,
  background: 'rgba(255,255,255,0.15)',
  margin: '10px 0',
};

function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return `${text.slice(0, maxLen)}…`;
}

function SkeletonLines() {
  return (
    <div className="w-full animate-pulse" style={{ padding: '0 16px' }}>
      <div
        style={{
          height: 20,
          borderRadius: 4,
          background: 'rgba(255,255,255,0.12)',
          marginBottom: 8,
        }}
      />
      <div
        style={{
          height: 14,
          borderRadius: 4,
          background: 'rgba(255,255,255,0.12)',
          marginBottom: 8,
        }}
      />
      <div
        style={{
          height: 14,
          borderRadius: 4,
          background: 'rgba(255,255,255,0.12)',
        }}
      />
    </div>
  );
}

interface StopTapProps {
  children: React.ReactNode;
  onTap: () => void;
  className?: string;
  style?: React.CSSProperties;
}

function StopTap({ children, onTap, className, style }: StopTapProps) {
  return (
    <div
      role="button"
      tabIndex={0}
      className={className}
      style={style}
      onClick={(e) => {
        e.stopPropagation();
        onTap();
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          e.stopPropagation();
          onTap();
        }
      }}
    >
      {children}
    </div>
  );
}

const VehicleCheckInCardBody: React.FC<VehicleCheckInCardBodyProps> = ({
  userEmail: _userEmail,
  userTier: _userTier,
}) => {
  const navigate = useNavigate();
  const { data, loading, error, refetch } = useVehicleDashboard();

  if (loading) {
    return <SkeletonLines />;
  }

  if (error) {
    return (
      <StopTap
        onTap={() => refetch()}
        className="w-full text-center"
        style={{ padding: '0 16px' }}
      >
        <p style={{ fontSize: 13, color: '#f5f3ff', margin: 0 }}>⚡ Couldn&apos;t load vehicle data</p>
        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', margin: '6px 0 0' }}>Tap to retry</p>
      </StopTap>
    );
  }

  if (!data || !data.hasVehicles) {
    return (
      <div className="w-full text-center" style={{ padding: '0 16px' }}>
        <div style={{ fontSize: 24, marginBottom: 8 }}>🚗</div>
        <p style={{ fontSize: 14, fontWeight: 600, color: '#f5f3ff', margin: 0 }}>No vehicles added yet</p>
        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', margin: '6px 0 0' }}>
          Add your vehicle to track costs and maintenance
        </p>
        <StopTap
          onTap={() => navigate('/dashboard/tools?tab=vehicle')}
          style={{
            display: 'inline-block',
            background: 'rgba(125,211,252,0.2)',
            border: '1px solid #7dd3fc',
            color: '#7dd3fc',
            borderRadius: 999,
            padding: '6px 14px',
            marginTop: 12,
            fontSize: 11,
            fontWeight: 700,
          }}
        >
          Add vehicle →
        </StopTap>
      </div>
    );
  }

  const vehicleName = data.primaryVehicle
    ? `${data.primaryVehicle.year} ${data.primaryVehicle.make} ${data.primaryVehicle.model}`
    : '—';
  const vehicleNameDisplay = truncate(vehicleName, 24);

  let subtext = '';
  if (data.totalVehicles > 1) {
    subtext = `+ ${data.totalVehicles - 1} more`;
  } else if (data.primaryVehicle?.currentMileage != null) {
    subtext = `${data.primaryVehicle.currentMileage.toLocaleString()} mi`;
  }

  const monthlyCostDisplay =
    data.totalMonthlyBudget > 0 ? `$${data.totalMonthlyBudget.toLocaleString()}` : 'Not set';

  const monthlyMilesDisplay =
    data.primaryVehicle?.monthlyMiles != null
      ? data.primaryVehicle.monthlyMiles.toLocaleString()
      : '—';

  let maintenanceRow: React.ReactNode;
  if (data.overdueMaintenanceCount > 0) {
    maintenanceRow = (
      <span
        style={{
          display: 'inline-block',
          background: 'rgba(252,165,165,0.2)',
          border: '1px solid #fca5a5',
          color: '#fca5a5',
          fontSize: 10,
          fontWeight: 700,
          borderRadius: 999,
          padding: '3px 10px',
        }}
      >
        ⚠ {data.overdueMaintenanceCount} overdue
      </span>
    );
  } else if (data.upcomingMaintenanceCount > 0 && data.nextMaintenance) {
    const desc = truncate(data.nextMaintenance.description, 22);
    maintenanceRow = (
      <span
        style={{
          display: 'inline-block',
          background: 'rgba(125,211,252,0.15)',
          border: '1px solid rgba(125,211,252,0.4)',
          color: '#7dd3fc',
          fontSize: 10,
          fontWeight: 600,
          borderRadius: 999,
          padding: '3px 10px',
        }}
      >
        → {desc} · ${data.nextMaintenance.estimatedCost.toLocaleString()}
      </span>
    );
  } else {
    maintenanceRow = (
      <span style={{ fontSize: 11, color: '#86efac' }}>✓ No maintenance due</span>
    );
  }

  return (
    <div style={{ padding: '0 16px', width: '100%' }}>
      <div>
        <p style={labelStyle}>YOUR VEHICLE</p>
        <p
          style={{
            fontSize: 16,
            fontWeight: 700,
            color: '#f5f3ff',
            margin: '4px 0 0',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {vehicleNameDisplay}
        </p>
        {subtext ? (
          <p style={{ fontSize: 11, color: '#ddd6fe', margin: '2px 0 0' }}>{subtext}</p>
        ) : null}
      </div>

      <div style={dividerStyle} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p style={labelStyle}>MONTHLY COST</p>
          <p style={{ fontSize: 14, fontWeight: 700, color: '#f5f3ff', margin: '4px 0 0' }}>
            {monthlyCostDisplay}
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <p style={labelStyle}>AVG MI/MONTH</p>
          <p style={{ fontSize: 14, fontWeight: 700, color: '#f5f3ff', margin: '4px 0 0' }}>
            {monthlyMilesDisplay}
          </p>
        </div>
      </div>

      <div style={dividerStyle} />

      <div style={{ marginTop: 10, textAlign: 'center' }}>{maintenanceRow}</div>

      <p
        style={{
          fontSize: 11,
          color: 'rgba(255,255,255,0.5)',
          textAlign: 'center',
          marginTop: 10,
          marginBottom: 0,
        }}
      >
        View vehicle details →
      </p>
    </div>
  );
};

export default VehicleCheckInCardBody;
