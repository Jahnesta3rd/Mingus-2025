import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useVibeTracker } from '../hooks/useVibeTracker';
import { useLifeLedger } from '../hooks/useLifeLedger';

export interface VibeRosterCardBodyProps {
  userEmail: string;
  userTier: 'budget' | 'mid_tier' | 'professional';
}

const labelStyle: React.CSSProperties = {
  fontSize: 9,
  color: '#e9d5ff',
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

function truncateNickname(nickname: string): string {
  if (nickname.length <= 14) return nickname;
  return `${nickname.slice(0, 14)}…`;
}

function vibeBarFillColor(score: number): string {
  if (score >= 70) return '#86efac';
  if (score >= 40) return '#fbbf24';
  return '#fca5a5';
}

function trendIndicator(trendDirection: string): { symbol: string; color: string } | null {
  if (trendDirection === 'improving') return { symbol: '↑', color: '#86efac' };
  if (trendDirection === 'declining') return { symbol: '↓', color: '#fca5a5' };
  if (trendDirection === 'stable') return { symbol: '→', color: '#ddd6fe' };
  return null;
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

const VibeRosterCardBody: React.FC<VibeRosterCardBodyProps> = ({
  userEmail: _userEmail,
  userTier: _userTier,
}) => {
  void _userEmail;
  void _userTier;

  const navigate = useNavigate();
  const {
    data: rosterData,
    loading: rosterLoading,
    error: rosterError,
    getPeople,
  } = useVibeTracker();
  const { profile, loading: vibeLoading } = useLifeLedger(true);

  useEffect(() => {
    void getPeople().catch(() => {
      /* error surfaced via hook */
    });
  }, [getPeople]);

  const loading = rosterLoading || vibeLoading;

  if (loading) {
    return <SkeletonLines />;
  }

  if (rosterError) {
    return (
      <div
        role="button"
        tabIndex={0}
        className="w-full text-center"
        style={{ padding: '0 16px' }}
        onClick={(e) => {
          e.stopPropagation();
          void getPeople().catch(() => {});
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            e.stopPropagation();
            void getPeople().catch(() => {});
          }
        }}
      >
        <div style={{ fontSize: 24, marginBottom: 8 }}>⚡</div>
        <p style={{ fontSize: 13, color: '#f5f3ff', margin: 0 }}>Couldn&apos;t load your roster</p>
        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', margin: '4px 0 0' }}>
          Tap to retry
        </p>
      </div>
    );
  }

  const activePeople = (rosterData ?? []).filter((p) => !p.is_archived);
  const displayPeople = activePeople.slice(0, 3);
  const vibeScore = profile?.vibe_score;

  if (activePeople.length === 0) {
    return (
      <div className="w-full text-center" style={{ padding: '0 16px' }}>
        <div style={{ fontSize: 24, marginBottom: 8 }}>👥</div>
        <p style={{ fontSize: 14, fontWeight: 600, color: '#f5f3ff', margin: 0 }}>
          Your roster is empty
        </p>
        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', margin: '4px 0 0' }}>
          Add people to track your relationships
        </p>
        <button
          type="button"
          style={{
            display: 'inline-block',
            borderRadius: 999,
            padding: '6px 14px',
            marginTop: 12,
            fontSize: 11,
            fontWeight: 700,
            background: 'rgba(196,181,253,0.2)',
            border: '1px solid #c4b5fd',
            color: '#c4b5fd',
            cursor: 'pointer',
          }}
          onClick={(e) => {
            e.stopPropagation();
            navigate('/dashboard/roster');
          }}
        >
          Add someone →
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: '0 16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <p style={labelStyle}>YOUR VIBE</p>
          <p
            style={{
              fontSize: 20,
              fontWeight: 800,
              color: '#f5f3ff',
              margin: '2px 0 0',
            }}
          >
            {vibeScore != null ? `${vibeScore}/100` : '—'}
          </p>
        </div>
        {vibeScore != null ? (
          <div
            style={{
              width: 80,
              height: 6,
              borderRadius: 999,
              background: 'rgba(255,255,255,0.15)',
              overflow: 'hidden',
              flexShrink: 0,
            }}
            aria-hidden
          >
            <div
              style={{
                width: (vibeScore / 100) * 80,
                height: 6,
                borderRadius: 999,
                background: vibeBarFillColor(vibeScore),
              }}
            />
          </div>
        ) : null}
      </div>

      <div style={dividerStyle} />

      {displayPeople.map((person) => {
        const annual = person.latest_assessment?.annual_projection;
        const monthlyCost =
          typeof annual === 'number' && annual > 0 ? Math.round(annual / 12) : null;
        const trend = person.trend?.trend_direction;
        const trendUi = trend ? trendIndicator(trend) : null;

        return (
          <div key={person.id} style={{ marginBottom: 8 }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  minWidth: 0,
                  flex: 1,
                }}
              >
                <span style={{ fontSize: 18, flexShrink: 0 }}>{person.emoji || '👤'}</span>
                <span
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: '#f5f3ff',
                    marginLeft: 6,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {truncateNickname(person.nickname)}
                </span>
              </div>
              <span style={{ fontSize: 14, flexShrink: 0, margin: '0 8px' }}>
                {person.latest_assessment?.verdict_emoji ?? '—'}
              </span>
              <span
                style={{
                  fontSize: 10,
                  flexShrink: 0,
                  color: monthlyCost != null ? '#ddd6fe' : 'rgba(255,255,255,0.4)',
                }}
              >
                {monthlyCost != null ? `~$${monthlyCost}/mo` : 'No checkup'}
              </span>
            </div>
            {trendUi ? (
              <div
                style={{
                  fontSize: 8,
                  marginLeft: 24,
                  marginTop: 2,
                  color: trendUi.color,
                }}
              >
                {trendUi.symbol}
              </div>
            ) : null}
          </div>
        );
      })}

      {activePeople.length > 3 ? (
        <p
          style={{
            fontSize: 10,
            color: 'rgba(255,255,255,0.5)',
            textAlign: 'right',
            margin: '4px 0 0',
          }}
        >
          + {activePeople.length - 3} more
        </p>
      ) : null}

      <p
        style={{
          fontSize: 11,
          color: 'rgba(255,255,255,0.5)',
          textAlign: 'center',
          margin: '8px 0 0',
        }}
      >
        View full roster →
      </p>
    </div>
  );
};

export default VibeRosterCardBody;
