import React from 'react';
import { CARD_CONFIGS } from './cardConfigs';

interface CardJobHomeProps {
  cardId: string;
  onBack: () => void;
  children: React.ReactNode;
}

const CardJobHome: React.FC<CardJobHomeProps> = ({ cardId, onBack, children }) => {
  const config = CARD_CONFIGS.find((c) => c.id === cardId);

  if (!config) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen flex-col">
      <div
        style={{
          height: 120,
          position: 'relative',
          background: config.backgroundColor,
          padding: '0 20px',
        }}
      >
        <button
          type="button"
          onClick={onBack}
          className="flex items-center gap-1"
          style={{
            position: 'absolute',
            top: 16,
            left: 16,
          }}
          aria-label="Back to Today"
        >
          <svg
            width={20}
            height={20}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ color: 'rgba(255,255,255,0.9)' }}
            aria-hidden
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          <span
            style={{
              fontSize: 13,
              color: 'rgba(255,255,255,0.9)',
              fontWeight: 600,
            }}
          >
            Today
          </span>
        </button>

        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            paddingBottom: 16,
          }}
        >
          <span
            style={{
              fontSize: 9,
              color: config.accentColor,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
            }}
          >
            {config.eyebrow}
          </span>
          <span
            style={{
              fontSize: 13,
              color: '#f5f3ff',
              fontWeight: 700,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            {config.label}
          </span>
        </div>

        <div
          style={{
            position: 'absolute',
            bottom: 16,
            right: 20,
            width: 36,
            height: 36,
            borderRadius: 8,
            background: 'rgba(255,255,255,0.18)',
            border: '1.5px solid rgba(255,255,255,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <svg
            width={18}
            height={18}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ color: '#f5f3ff' }}
            aria-hidden
          >
            <path d={config.iconPath} />
          </svg>
        </div>
      </div>

      <div
        className="flex-1 overflow-y-auto"
        style={{
          background: '#FAF5FF',
          paddingBottom: 80,
        }}
      >
        {children}
      </div>
    </div>
  );
};

export default CardJobHome;
