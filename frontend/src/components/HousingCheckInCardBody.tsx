import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useHousingCheckIn } from '../hooks/useHousingCheckIn';

export interface HousingCheckInCardBodyProps {
  userEmail: string;
  userTier: 'budget' | 'mid_tier' | 'professional';
}

const labelStyle: React.CSSProperties = {
  fontSize: 9,
  color: '#fbbf24',
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

const pillBase: React.CSSProperties = {
  display: 'inline-block',
  borderRadius: 999,
  cursor: 'pointer',
};

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

const HousingCheckInCardBody: React.FC<HousingCheckInCardBodyProps> = ({
  userEmail: _userEmail,
  userTier: _userTier,
}) => {
  const navigate = useNavigate();
  const { data, loading, error, refetch } = useHousingCheckIn();

  if (loading) {
    return <SkeletonLines />;
  }

  if (error) {
    return (
      <StopTap
        className="w-full text-center"
        style={{ padding: '0 16px' }}
        onTap={() => void refetch()}
      >
        <div style={{ fontSize: 24, marginBottom: 8 }} aria-hidden>
          ⚡
        </div>
        <p style={{ fontSize: 13, color: '#f5f3ff', margin: 0 }}>
          Couldn&apos;t load housing data
        </p>
        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', margin: '6px 0 0' }}>
          Tap to retry
        </p>
      </StopTap>
    );
  }

  if (!data || !data.profileComplete) {
    return (
      <div className="w-full text-center" style={{ padding: '0 16px' }}>
        <div style={{ fontSize: 24, marginBottom: 8 }} aria-hidden>
          🏠
        </div>
        <p style={{ fontSize: 14, fontWeight: 600, color: '#f5f3ff', margin: 0 }}>
          Complete your housing profile
        </p>
        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', margin: '6px 0 0' }}>
          Add your housing details to track costs
        </p>
        <StopTap
          onTap={() => navigate('/dashboard/tools?tab=housing')}
          style={{
            ...pillBase,
            background: 'rgba(251,191,36,0.2)',
            border: '1px solid #fbbf24',
            color: '#fbbf24',
            padding: '6px 14px',
            marginTop: 12,
            fontSize: 11,
            fontWeight: 700,
          }}
        >
          Set up housing →
        </StopTap>
      </div>
    );
  }

  const housingTypeLabel =
    data.housingType === 'rent'
      ? 'Renting'
      : data.housingType === 'own'
        ? 'Homeowner'
        : '—';
  const monthlyLabel = data.housingType === 'rent' ? 'MONTHLY RENT' : 'MONTHLY COST';
  const monthlyValue =
    data.monthlyCost != null ? `$${data.monthlyCost.toLocaleString()}` : 'Not set';
  const buyGoalColor = data.hasBuyGoal ? '#86efac' : '#ddd6fe';

  return (
    <div className="w-full self-stretch text-left" style={{ padding: '0 16px' }}>
      <div>
        <p style={labelStyle}>Your housing</p>
        <p
          style={{
            marginTop: 4,
            fontSize: 16,
            fontWeight: 700,
            color: '#f5f3ff',
            marginBottom: 0,
            lineHeight: 1.2,
          }}
        >
          {housingTypeLabel}
        </p>
        <p style={{ fontSize: 11, color: '#ddd6fe', margin: '4px 0 0' }}>
          {data.zipOrCity ?? 'Location not set'}
        </p>
      </div>

      <div style={dividerStyle} aria-hidden />

      <div className="flex items-start justify-between gap-3">
        <div>
          <p style={labelStyle}>{monthlyLabel}</p>
          <p
            style={{
              marginTop: 4,
              fontSize: 14,
              fontWeight: 700,
              color: '#f5f3ff',
              marginBottom: 0,
            }}
          >
            {monthlyValue}
          </p>
        </div>
        <div className="text-right">
          <p style={labelStyle}>Buy goal</p>
          <p
            style={{
              marginTop: 4,
              fontSize: 14,
              fontWeight: 700,
              color: buyGoalColor,
              marginBottom: 0,
            }}
          >
            {data.hasBuyGoal ? 'Yes ✓' : 'Not set'}
          </p>
        </div>
      </div>

      <div style={dividerStyle} aria-hidden />

      {data.hasBuyGoal && data.targetPrice != null ? (
        <div style={{ marginTop: 8 }}>
          <p style={labelStyle}>Target price</p>
          <p
            style={{
              marginTop: 4,
              fontSize: 14,
              fontWeight: 700,
              color: '#f5f3ff',
              marginBottom: 0,
            }}
          >
            ${Math.round(data.targetPrice / 1000)}K
          </p>
          {data.targetTimelineMonths != null && (
            <p style={{ fontSize: 11, color: '#ddd6fe', margin: '4px 0 0' }}>
              {Math.round(data.targetTimelineMonths / 12)} yr timeline
            </p>
          )}
        </div>
      ) : data.housingType === 'rent' ? (
        <div className="text-center" style={{ marginTop: 10 }}>
          <StopTap
            onTap={() => navigate('/dashboard/tools?tab=housing')}
            style={{
              ...pillBase,
              background: 'rgba(251,191,36,0.15)',
              border: '1px solid rgba(251,191,36,0.4)',
              color: '#fbbf24',
              fontSize: 10,
              fontWeight: 600,
              padding: '3px 10px',
            }}
          >
            → Explore buying options
          </StopTap>
        </div>
      ) : (
        <p
          className="text-center"
          style={{ fontSize: 11, color: '#86efac', marginTop: 10, marginBottom: 0 }}
        >
          ✓ Homeowner
        </p>
      )}

      <p
        style={{
          fontSize: 11,
          color: 'rgba(255,255,255,0.5)',
          textAlign: 'center',
          marginTop: 10,
          marginBottom: 0,
        }}
      >
        View housing details →
      </p>
    </div>
  );
};

export default HousingCheckInCardBody;
