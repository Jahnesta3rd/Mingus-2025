import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useCashForecast } from '../hooks/useCashForecast';

export interface CashSnapshotCardBodyProps {
  userEmail: string;
  userTier: 'budget' | 'mid_tier' | 'professional';
}

function formatUsd(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(Number.isFinite(value) ? value : 0);
}

function formatNetChange(netChange: number): { text: string; color: string } {
  if (netChange === 0) {
    return { text: '—', color: '#ddd6fe' };
  }
  const abs = formatUsd(Math.abs(netChange));
  if (netChange > 0) {
    return { text: `+${abs}`, color: '#86efac' };
  }
  return { text: `-${abs}`, color: '#fca5a5' };
}

const labelStyle: React.CSSProperties = {
  fontSize: 9,
  color: '#6ee7b7',
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  margin: 0,
  fontWeight: 600,
};

const dividerStyle: React.CSSProperties = {
  height: 1,
  background: 'rgba(255,255,255,0.15)',
  margin: '12px 0',
};

function SkeletonLines() {
  return (
    <div className="w-full animate-pulse" style={{ padding: '0 16px' }}>
      <div style={{ height: 20, borderRadius: 4, background: 'rgba(255,255,255,0.12)', marginBottom: 8 }} />
      <div style={{ height: 14, borderRadius: 4, background: 'rgba(255,255,255,0.12)', marginBottom: 8 }} />
      <div style={{ height: 14, borderRadius: 4, background: 'rgba(255,255,255,0.12)' }} />
    </div>
  );
}

interface TapMessageProps {
  emoji: string;
  text: string;
  subtext: string;
  onTap: () => void;
}

function TapMessage({ emoji, text, subtext, onTap }: TapMessageProps) {
  return (
    <div
      role="button"
      tabIndex={0}
      className="w-full text-center"
      style={{ padding: '0 16px' }}
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
      <div style={{ fontSize: 24, marginBottom: 8 }}>{emoji}</div>
      <p style={{ fontSize: 14, fontWeight: 600, color: '#f5f3ff', margin: 0 }}>{text}</p>
      <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', margin: '6px 0 0' }}>{subtext}</p>
    </div>
  );
}

function statusBadgeStyle(status: 'healthy' | 'warning' | 'danger'): {
  background: string;
  border: string;
  color: string;
  label: string;
} {
  switch (status) {
    case 'warning':
      return {
        background: 'rgba(251,191,36,0.2)',
        border: '1px solid #fbbf24',
        color: '#fbbf24',
        label: 'WATCH THIS',
      };
    case 'danger':
      return {
        background: 'rgba(252,165,165,0.2)',
        border: '1px solid #fca5a5',
        color: '#fca5a5',
        label: 'NEEDS ATTENTION',
      };
    default:
      return {
        background: 'rgba(134,239,172,0.2)',
        border: '1px solid #86efac',
        color: '#86efac',
        label: 'ON TRACK',
      };
  }
}

const CashSnapshotCardBody: React.FC<CashSnapshotCardBodyProps> = ({
  userEmail,
  userTier: _userTier,
}) => {
  void _userTier;
  const navigate = useNavigate();
  const { data, loading, error, refetch } = useCashForecast(userEmail);

  if (loading) {
    return <SkeletonLines />;
  }

  if (error) {
    return (
      <TapMessage
        emoji="⚡"
        text="Couldn't load forecast"
        subtext="Tap to retry"
        onTap={() => void refetch()}
      />
    );
  }

  if (!data || !data.balanceSet) {
    return (
      <TapMessage
        emoji="💳"
        text="Set your starting balance"
        subtext="Tap to set up your forecast"
        onTap={() => navigate('/dashboard/forecast')}
      />
    );
  }

  const net = formatNetChange(data.netChange);
  const badge = statusBadgeStyle(data.balanceStatus);

  return (
    <div className="w-full self-stretch text-left" style={{ padding: '0 16px' }}>
      <div>
        <p style={labelStyle}>Today&apos;s Balance</p>
        <p
          style={{
            marginTop: 4,
            fontSize: 28,
            fontWeight: 800,
            color: '#f5f3ff',
            marginBottom: 0,
            lineHeight: 1.1,
          }}
        >
          {formatUsd(data.todayBalance)}
        </p>
      </div>

      <div style={dividerStyle} aria-hidden />

      <div className="flex items-start justify-between gap-3">
        <div>
          <p style={labelStyle}>30-Day Forecast</p>
          <p
            style={{
              marginTop: 4,
              fontSize: 18,
              fontWeight: 700,
              color: '#f5f3ff',
              marginBottom: 0,
            }}
          >
            {formatUsd(data.balance30Day)}
          </p>
        </div>
        <div className="text-right">
          <p style={labelStyle}>Net Change</p>
          <p
            style={{
              marginTop: 4,
              fontSize: 18,
              fontWeight: 700,
              color: net.color,
              marginBottom: 0,
            }}
          >
            {net.text}
          </p>
        </div>
      </div>

      <div style={dividerStyle} aria-hidden />

      <div className="flex justify-center" style={{ marginTop: 10 }}>
        <span
          style={{
            display: 'inline-block',
            borderRadius: 999,
            padding: '4px 12px',
            background: badge.background,
            border: badge.border,
            color: badge.color,
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
          }}
        >
          {badge.label}
        </span>
      </div>

      <p
        style={{
          marginTop: 10,
          fontSize: 11,
          color: 'rgba(255,255,255,0.5)',
          textAlign: 'center',
          marginBottom: 0,
        }}
      >
        View full forecast →
      </p>
    </div>
  );
};

export default CashSnapshotCardBody;
