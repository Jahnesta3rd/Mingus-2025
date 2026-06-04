import React from 'react';

export interface HeroCardProps {
  cardIndex: number;
  totalCards: number;
  label: string;
  eyebrow: string;
  backgroundColor?: string;
  accentColor?: string;
  icon: React.ReactNode;
  onTap?: () => void;
  children: React.ReactNode;
  className?: string;
}

function titleCaseLabel(label: string): string {
  return label
    .toLowerCase()
    .split(/\s+/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function eyebrowColor(backgroundColor?: string): string {
  const bg = backgroundColor ?? '#FAF5FF';
  if (bg.includes('gradient') || bg.startsWith('#1') || bg.startsWith('#2') || bg.startsWith('#3')) {
    return 'rgba(255,255,255,0.55)';
  }
  return '#5B2D8E';
}

const HeroCard: React.FC<HeroCardProps> = ({
  label,
  eyebrow,
  backgroundColor = '#FAF5FF',
  accentColor = '#5B2D8E',
  icon,
  onTap,
  children,
  className = '',
}) => {
  const cardTitle = titleCaseLabel(label);

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onTap}
      onKeyDown={(e) => {
        if (onTap && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onTap();
        }
      }}
      className={`relative h-full cursor-pointer overflow-hidden rounded-[24px] transition-transform duration-[250ms] ease-in-out hover:-translate-y-0.5 ${className}`.trim()}
      style={{
        background: backgroundColor,
        boxShadow:
          '0 4px 12px rgba(59,31,110,0.12), 0 16px 40px rgba(59,31,110,0.18)',
      }}
    >
      <div
        className="absolute left-0 right-0 top-0"
        style={{ padding: '16px 16px 0' }}
      >
        <p
          className="uppercase"
          style={{
            fontSize: 9,
            fontWeight: 700,
            letterSpacing: '0.14em',
            color: eyebrowColor(backgroundColor),
            margin: 0,
          }}
        >
          {eyebrow}
        </p>
        <p
          className="mt-1 uppercase"
          style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: '0.12em',
            color: accentColor,
            margin: 0,
          }}
        >
          {label}
        </p>
      </div>

      <div className="flex h-full flex-col items-center justify-center px-6 pt-16 pb-32">
        {children}
      </div>

      <div
        className="absolute flex items-center justify-center"
        style={{
          bottom: 90,
          left: 12,
          width: 36,
          height: 36,
          borderRadius: 9,
          background: 'rgba(255,255,255,0.18)',
          border: '1.5px solid rgba(255,255,255,0.4)',
        }}
      >
        {icon}
      </div>

      <p
        className="absolute"
        style={{
          bottom: 72,
          right: 16,
          fontSize: 10,
          color: 'rgba(255,255,255,0.5)',
          margin: 0,
        }}
      >
        Tap to open →
      </p>

      <div
        className="absolute bottom-0 left-0 right-0"
        style={{ padding: '14px 16px 18px' }}
      >
        <p
          style={{
            fontFamily: '"Fraunces", Georgia, serif',
            fontSize: 17,
            fontWeight: 600,
            letterSpacing: '-0.015em',
            color: '#f5f3ff',
            margin: 0,
            lineHeight: 1.25,
          }}
        >
          {cardTitle}
        </p>
        <p
          style={{
            fontSize: 11,
            color: '#ddd6fe',
            lineHeight: 1.35,
            margin: '4px 0 0',
          }}
        >
          {eyebrow}
        </p>
      </div>
    </div>
  );
};

export default HeroCard;
