import React from 'react';
import { CARD_CONFIGS } from './cardConfigs';

interface CardJobHomeProps {
  cardId: string;
  onBack: () => void;
  children: React.ReactNode;
}

function extractBaseColor(gradient: string): string {
  const match = gradient.match(/#[0-9a-fA-F]{6}/);
  return match ? match[0] : '#1a1a2e';
}

const CardJobHome: React.FC<CardJobHomeProps> = ({ cardId, onBack, children }) => {
  const config = CARD_CONFIGS.find((c) => c.id === cardId);

  if (!config) {
    return <>{children}</>;
  }

  const baseColor = extractBaseColor(config.backgroundColor);

  return (
    <div style={{ minHeight: '100vh', background: baseColor }}>
      {/* Header — normal document flow, not fixed or sticky */}
      <div
        style={{
          height: 100,
          background: config.backgroundColor,
          padding: '0 20px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          paddingTop: 16,
          paddingBottom: 16,
        }}
      >
        {/* Back button row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <button
            type="button"
            onClick={onBack}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 0,
            }}
            aria-label="Back to Today"
          >
            <svg
              width={22}
              height={22}
              viewBox="0 0 24 24"
              fill="none"
              stroke="#ffffff"
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden
            >
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            <span
              style={{
                fontSize: 14,
                color: '#ffffff',
                fontWeight: 700,
                textShadow: '0 1px 4px rgba(0,0,0,0.5)',
              }}
            >
              Today
            </span>
          </button>
        </div>

        {/* Card identity row */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <span
            style={{
              fontSize: 10,
              color: '#ffffff',
              fontWeight: 700,
              letterSpacing: '0.14em',
              textTransform: 'uppercase',
              textShadow: '0 1px 4px rgba(0,0,0,0.5)',
              opacity: 0.85,
            }}
          >
            {config.eyebrow}
          </span>
          <span
            style={{
              fontSize: 15,
              color: '#ffffff',
              fontWeight: 800,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              textShadow: '0 1px 4px rgba(0,0,0,0.5)',
            }}
          >
            {config.label}
          </span>
        </div>
      </div>

      {/* Content */}
      <div style={{ paddingBottom: 80 }}>{children}</div>
    </div>
  );
};

export default CardJobHome;
