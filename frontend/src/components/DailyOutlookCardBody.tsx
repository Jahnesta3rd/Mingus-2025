import React from 'react';
import { useDailyOutlookCache } from '../hooks/useDailyOutlookCache';

export interface DailyOutlookCardBodyProps {
  userEmail: string;
  userTier: 'budget' | 'mid_tier' | 'professional';
}

function insightPrefix(icon: string | undefined): string {
  const raw = icon?.trim();
  if (!raw) return '';
  return `${raw} `;
}

function formatChangePercentage(
  trend: 'up' | 'down' | 'stable',
  changePercentage: number
): { label: string; color: string } {
  const pct = Math.abs(changePercentage);
  const formatted = Number.isInteger(pct) ? `${pct}` : pct.toFixed(1);

  if (trend === 'up') {
    return { label: `▲ +${formatted}%`, color: '#86efac' };
  }
  if (trend === 'down') {
    return { label: `▼ -${formatted}%`, color: '#fca5a5' };
  }
  return { label: `— ${formatted}%`, color: '#ddd6fe' };
}

function truncateText(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text;
  return `${text.slice(0, maxChars - 1)}…`;
}

const lineClamp2: React.CSSProperties = {
  display: '-webkit-box',
  WebkitLineClamp: 2,
  WebkitBoxOrient: 'vertical',
  overflow: 'hidden',
};

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

interface StatusMessageProps {
  emoji: string;
  text: string;
  subtext: string;
  onRetry: () => void;
}

function StatusMessage({ emoji, text, subtext, onRetry }: StatusMessageProps) {
  return (
    <div
      role="button"
      tabIndex={0}
      className="w-full text-center"
      style={{ padding: '0 16px' }}
      onClick={(e) => {
        e.stopPropagation();
        onRetry();
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          e.stopPropagation();
          onRetry();
        }
      }}
    >
      <div style={{ fontSize: 24, marginBottom: 8 }}>{emoji}</div>
      <p style={{ fontSize: 13, color: '#ddd6fe', margin: 0 }}>{text}</p>
      <p
        style={{
          fontSize: 11,
          color: 'rgba(255,255,255,0.5)',
          margin: '6px 0 0',
        }}
      >
        {subtext}
      </p>
    </div>
  );
}

const DailyOutlookCardBody: React.FC<DailyOutlookCardBodyProps> = ({
  userEmail: _userEmail,
  userTier: _userTier,
}) => {
  void _userEmail;
  void _userTier;

  const { data, loading, error, refetch } = useDailyOutlookCache();

  if (loading) {
    return <SkeletonLines />;
  }

  if (error) {
    return (
      <StatusMessage
        emoji="⚡"
        text="Couldn't load your outlook"
        subtext="Tap to retry"
        onRetry={() => void refetch()}
      />
    );
  }

  if (!data) {
    return (
      <StatusMessage
        emoji="🌅"
        text="Your outlook is being prepared"
        subtext="Check back in a moment"
        onRetry={() => void refetch()}
      />
    );
  }

  const trend = formatChangePercentage(
    data.balance_score.trend,
    data.balance_score.change_percentage
  );
  const firstAction = data.quick_actions[0];
  const encouragementSubtext = `${data.encouragement_message.emoji} ${truncateText(
    data.encouragement_message.text,
    18
  )}`.trim();

  return (
    <div className="w-full self-stretch text-left" style={{ padding: '0 16px' }}>
      <p
        style={{
          fontSize: 15,
          fontWeight: 700,
          color: '#f5f3ff',
          margin: 0,
          lineHeight: 1.35,
          ...lineClamp2,
        }}
      >
        {insightPrefix(data.primary_insight.icon)}
        {data.primary_insight.title}
      </p>

      <p
        style={{
          fontSize: 12,
          color: '#ddd6fe',
          lineHeight: 1.4,
          margin: '6px 0 0',
          ...lineClamp2,
        }}
      >
        {data.primary_insight.message}
      </p>

      <div
        style={{
          height: 1,
          background: 'rgba(255,255,255,0.15)',
          margin: '10px 0',
        }}
      />

      <div className="flex items-start justify-between gap-3">
        <div>
          <p
            style={{
              fontSize: 9,
              color: '#c4b5fd',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              margin: 0,
              fontWeight: 600,
            }}
          >
            BALANCE
          </p>
          <p
            style={{
              fontSize: 22,
              fontWeight: 800,
              color: '#f5f3ff',
              margin: '2px 0 0',
              lineHeight: 1.1,
            }}
          >
            {data.balance_score.value}
          </p>
          <p
            style={{
              fontSize: 10,
              fontWeight: 600,
              color: trend.color,
              margin: '2px 0 0',
            }}
          >
            {trend.label}
          </p>
        </div>

        <div className="text-right">
          <p
            style={{
              fontSize: 9,
              color: '#c4b5fd',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              margin: 0,
              fontWeight: 600,
            }}
          >
            STREAK
          </p>
          <p
            style={{
              fontSize: 22,
              fontWeight: 800,
              color: '#fbbf24',
              margin: '2px 0 0',
              lineHeight: 1.1,
            }}
          >
            {data.streak_data.current_streak} days
          </p>
          <p
            style={{
              fontSize: 10,
              color: 'rgba(255,255,255,0.6)',
              margin: '2px 0 0',
            }}
          >
            {encouragementSubtext}
          </p>
        </div>
      </div>

      {firstAction ? (
        <div
          style={{
            background: 'rgba(255,255,255,0.1)',
            borderRadius: 8,
            padding: '8px 10px',
            marginTop: 10,
          }}
        >
          <p
            style={{
              fontSize: 11,
              color: '#f5f3ff',
              fontWeight: 600,
              margin: 0,
            }}
          >
            → {firstAction.title}
          </p>
          <p
            style={{
              fontSize: 10,
              color: '#c4b5fd',
              margin: '2px 0 0',
            }}
          >
            {firstAction.estimated_time}
          </p>
        </div>
      ) : null}
    </div>
  );
};

export default DailyOutlookCardBody;
