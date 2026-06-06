import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useCareerCheckIn } from '../hooks/useCareerCheckIn';

export interface CareerCheckInCardBodyProps {
  userEmail: string;
  userTier: 'budget' | 'mid_tier' | 'professional';
}

const labelStyle: React.CSSProperties = {
  fontSize: 9,
  color: '#a5b4fc',
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
  padding: '6px 14px',
  marginTop: 12,
  fontSize: 11,
  fontWeight: 700,
  cursor: 'pointer',
};

function truncateRole(role: string, maxLen = 28): string {
  if (role.length <= maxLen) return role;
  return `${role.slice(0, maxLen)}…`;
}

function SkeletonLines() {
  return (
    <div className="w-full animate-pulse" style={{ padding: '0 16px' }}>
      <div
        style={{
          height: 16,
          borderRadius: 4,
          background: 'rgba(255,255,255,0.12)',
          marginBottom: 8,
        }}
      />
      <div
        style={{
          height: 12,
          borderRadius: 4,
          background: 'rgba(255,255,255,0.12)',
          marginBottom: 8,
        }}
      />
      <div
        style={{
          height: 12,
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

const CareerCheckInCardBody: React.FC<CareerCheckInCardBodyProps> = ({
  userEmail,
  userTier,
}) => {
  const navigate = useNavigate();
  const { data, loading, error, refetch } = useCareerCheckIn(userEmail, userTier);

  if (userTier === 'budget') {
    return (
      <StopTap
        className="w-full text-center"
        style={{ padding: '0 16px' }}
        onTap={() => navigate('/dashboard/tools?tab=billing')}
      >
        <div style={{ fontSize: 24, marginBottom: 8 }} aria-hidden>
          🔒
        </div>
        <p style={{ fontSize: 14, fontWeight: 600, color: '#f5f3ff', margin: 0 }}>
          Career insights are a Mid-Tier feature
        </p>
        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', margin: '6px 0 0' }}>
          Upgrade to see job matches and income projections
        </p>
        <span
          style={{
            ...pillBase,
            background: 'rgba(251,191,36,0.2)',
            border: '1px solid #fbbf24',
            color: '#fbbf24',
          }}
        >
          Upgrade now →
        </span>
      </StopTap>
    );
  }

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
          Couldn&apos;t load career data
        </p>
        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', margin: '6px 0 0' }}>
          Tap to retry
        </p>
      </StopTap>
    );
  }

  if (!data || !data.profileComplete) {
    return (
      <StopTap
        className="w-full text-center"
        style={{ padding: '0 16px' }}
        onTap={() => navigate('/dashboard/tools?tab=recommendations')}
      >
        <div style={{ fontSize: 24, marginBottom: 8 }} aria-hidden>
          💼
        </div>
        <p style={{ fontSize: 14, fontWeight: 600, color: '#f5f3ff', margin: 0 }}>
          Complete your career profile
        </p>
        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', margin: '6px 0 0' }}>
          Add your role and industry to unlock job matches
        </p>
        <span
          style={{
            ...pillBase,
            background: 'rgba(165,180,252,0.2)',
            border: '1px solid #a5b4fc',
            color: '#a5b4fc',
          }}
        >
          Set up career →
        </span>
      </StopTap>
    );
  }

  const roleDisplay = data.currentRole ? truncateRole(data.currentRole) : '—';
  const targetCompDisplay =
    data.targetComp != null
      ? `$${Math.round(data.targetComp / 1000)}K`
      : 'Not set';
  const openColor = data.openToMove ? '#86efac' : '#ddd6fe';

  return (
    <div className="w-full self-stretch text-left" style={{ padding: '0 16px' }}>
      <div>
        <p style={labelStyle}>Your role</p>
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
          {roleDisplay}
        </p>
        <p style={{ fontSize: 11, color: '#ddd6fe', margin: '4px 0 0' }}>
          {data.industry ?? '—'}
        </p>
      </div>

      <div style={dividerStyle} aria-hidden />

      <div className="flex items-start justify-between gap-3">
        <div>
          <p style={labelStyle}>Level</p>
          <p
            style={{
              marginTop: 4,
              fontSize: 14,
              fontWeight: 700,
              color: '#f5f3ff',
              marginBottom: 0,
            }}
          >
            {data.seniorityLevel ?? '—'}
          </p>
        </div>
        <div className="text-right">
          <p style={labelStyle}>Experience</p>
          <p
            style={{
              marginTop: 4,
              fontSize: 14,
              fontWeight: 700,
              color: '#f5f3ff',
              marginBottom: 0,
            }}
          >
            {data.yearsExperience != null ? `${data.yearsExperience} yrs` : '—'}
          </p>
        </div>
      </div>

      <div style={dividerStyle} aria-hidden />

      <div className="flex items-start justify-between gap-3">
        <div>
          <p style={labelStyle}>Target comp</p>
          <p
            style={{
              marginTop: 4,
              fontSize: 14,
              fontWeight: 700,
              color: '#f5f3ff',
              marginBottom: 0,
            }}
          >
            {targetCompDisplay}
          </p>
        </div>
        <div className="text-right">
          <p style={labelStyle}>Open to move</p>
          <p
            style={{
              marginTop: 4,
              fontSize: 14,
              fontWeight: 700,
              color: openColor,
              marginBottom: 0,
            }}
          >
            {data.openToMove ? 'Yes ✓' : 'No'}
          </p>
        </div>
      </div>

      <p
        style={{
          fontSize: 11,
          color: 'rgba(255,255,255,0.5)',
          textAlign: 'center',
          marginTop: 10,
          marginBottom: 0,
        }}
      >
        See job matches →
      </p>
    </div>
  );
};

export default CareerCheckInCardBody;
