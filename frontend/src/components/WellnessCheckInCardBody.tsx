import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useWellnessData } from '../hooks/useWellnessData';

export interface WellnessCheckInCardBodyProps {
  userEmail: string;
  userTier: 'budget' | 'mid_tier' | 'professional';
}

const labelStyle: React.CSSProperties = {
  fontSize: 9,
  color: '#86efac',
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
  margin: 0,
  fontWeight: 600,
};

const scoreLabelStyle: React.CSSProperties = {
  ...labelStyle,
  letterSpacing: '0.1em',
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

function getTierLabel(score: number): string {
  if (score >= 75) return 'Thriving';
  if (score >= 50) return 'Growing';
  if (score >= 25) return 'Building';
  return 'Needs attention';
}

function getTierColor(score: number): string {
  if (score >= 75) return '#86efac';
  if (score >= 50) return '#fbbf24';
  if (score >= 25) return '#ddd6fe';
  return '#fca5a5';
}

function formatScore(value: number | null | undefined): number {
  if (value == null || Number.isNaN(Number(value))) return 0;
  return Math.round(Number(value));
}

function formatChange(change: number | null | undefined): React.ReactNode {
  const n = change == null || Number.isNaN(Number(change)) ? 0 : Number(change);
  if (n > 0) {
    return (
      <span style={{ fontSize: 10, color: '#86efac', marginTop: 2, display: 'block' }}>
        ▲ +{Math.round(n)}
      </span>
    );
  }
  if (n < 0) {
    return (
      <span style={{ fontSize: 10, color: '#fca5a5', marginTop: 2, display: 'block' }}>
        ▼ {Math.round(n)}
      </span>
    );
  }
  return (
    <span style={{ fontSize: 10, color: '#ddd6fe', marginTop: 2, display: 'block' }}>
      — no change
    </span>
  );
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

const WellnessCheckInCardBody: React.FC<WellnessCheckInCardBodyProps> = ({
  userEmail: _userEmail,
  userTier: _userTier,
}) => {
  const navigate = useNavigate();
  const { scores, hasRealScores, streak, weeksOfData, loading, error, refetch } =
    useWellnessData();

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
          Couldn&apos;t load wellness data
        </p>
        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', margin: '6px 0 0' }}>
          Tap to retry
        </p>
      </StopTap>
    );
  }

  if (!scores || !hasRealScores) {
    const subtext =
      weeksOfData === 0
        ? 'Complete your first check-in to see your score'
        : weeksOfData < 4
          ? `${weeksOfData} of 4 weeks to unlock insights`
          : 'Check in to update your score';

    return (
      <div className="w-full text-center" style={{ padding: '0 16px' }}>
        <div style={{ fontSize: 24, marginBottom: 8 }} aria-hidden>
          🌱
        </div>
        <p style={{ fontSize: 14, fontWeight: 600, color: '#f5f3ff', margin: 0 }}>
          Start your wellness check-in
        </p>
        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', margin: '6px 0 0' }}>
          {subtext}
        </p>
        {weeksOfData > 0 && weeksOfData < 4 ? (
          <div
            style={{
              marginTop: 8,
              width: '100%',
              height: 4,
              borderRadius: 999,
              background: 'rgba(255,255,255,0.15)',
              overflow: 'hidden',
            }}
            aria-hidden
          >
            <div
              style={{
                height: '100%',
                width: `${(weeksOfData / 4) * 100}%`,
                background: '#86efac',
                borderRadius: 999,
              }}
            />
          </div>
        ) : null}
        <StopTap
          onTap={() => navigate('/dashboard/tools?tab=wellness')}
          style={{
            ...pillBase,
            background: 'rgba(134,239,172,0.2)',
            border: '1px solid #86efac',
            color: '#86efac',
            padding: '6px 14px',
            marginTop: 12,
            fontSize: 11,
            fontWeight: 700,
          }}
        >
          Take check-in →
        </StopTap>
      </div>
    );
  }

  const overall = formatScore(scores.overall_wellness_score);
  const tierLabel = getTierLabel(overall);
  const tierColor = getTierColor(overall);

  const categories = [
    { label: 'PHYSICAL', value: formatScore(scores.physical_score) },
    { label: 'MENTAL', value: formatScore(scores.mental_score) },
    { label: 'RELATIONAL', value: formatScore(scores.relational_score) },
    { label: 'FINANCIAL', value: formatScore(scores.financial_feeling_score) },
  ];

  return (
    <div className="w-full self-stretch text-left" style={{ padding: '0 16px' }}>
      <div>
        <p style={scoreLabelStyle}>Wellness score</p>
        <div className="flex items-baseline flex-wrap" style={{ marginTop: 4 }}>
          <span
            style={{
              fontSize: 28,
              fontWeight: 800,
              color: '#f5f3ff',
              lineHeight: 1.1,
            }}
          >
            {overall}
          </span>
          <span
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: tierColor,
              marginLeft: 8,
            }}
          >
            {tierLabel}
          </span>
        </div>
        {formatChange(scores.overall_change)}
      </div>

      <div style={dividerStyle} aria-hidden />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 8,
        }}
      >
        {categories.map((cat) => (
          <div key={cat.label}>
            <p style={labelStyle}>{cat.label}</p>
            <p
              style={{
                marginTop: 4,
                fontSize: 14,
                fontWeight: 700,
                color: '#f5f3ff',
                marginBottom: 0,
              }}
            >
              {cat.value}
            </p>
          </div>
        ))}
      </div>

      <div style={dividerStyle} aria-hidden />

      <div className="text-center" style={{ marginTop: 8 }}>
        {streak && streak.current_streak > 0 ? (
          <p
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: '#fbbf24',
              margin: 0,
            }}
          >
            🔥 {streak.current_streak} week streak
          </p>
        ) : (
          <p
            style={{
              fontSize: 11,
              color: 'rgba(255,255,255,0.5)',
              margin: 0,
            }}
          >
            Start your streak this week
          </p>
        )}
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
        View full wellness →
      </p>
    </div>
  );
};

export default WellnessCheckInCardBody;
