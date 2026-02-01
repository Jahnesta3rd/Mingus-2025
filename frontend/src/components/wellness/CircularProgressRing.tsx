import React, { useEffect, useState } from 'react';

export interface CircularProgressRingProps {
  /** Score 0-100 */
  value: number;
  /** Ring size in pixels */
  size?: number;
  /** Stroke width */
  strokeWidth?: number;
  /** CSS color for the progress stroke (e.g. #10B981) */
  color?: string;
  /** Background track color */
  trackColor?: string;
  /** Optional pulse animation */
  pulse?: boolean;
  /** Duration of value animation in ms */
  animationDuration?: number;
  className?: string;
  /** Accessible label */
  ariaLabel?: string;
}

const DEFAULT_SIZE = 160;
const DEFAULT_STROKE = 10;
const DEFAULT_DURATION = 1200;

/**
 * Animated SVG circular progress ring (0-100).
 * Optional count-up animation and subtle pulse.
 */
export const CircularProgressRing: React.FC<CircularProgressRingProps> = ({
  value,
  size = DEFAULT_SIZE,
  strokeWidth = DEFAULT_STROKE,
  color = '#8b5cf6',
  trackColor = 'rgba(148, 163, 184, 0.2)',
  pulse = false,
  animationDuration = DEFAULT_DURATION,
  className = '',
  ariaLabel,
}) => {
  const [displayValue, setDisplayValue] = useState(0);
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const clamped = Math.min(100, Math.max(0, value));

  useEffect(() => {
    if (animationDuration <= 0) {
      setDisplayValue(clamped);
      return;
    }
    const start = performance.now();
    const startValue = 0;
    const raf = (now: number) => {
      const elapsed = now - start;
      const t = Math.min(1, elapsed / animationDuration);
      const eased = 1 - (1 - t) * (1 - t);
      setDisplayValue(Math.round(startValue + (clamped - startValue) * eased));
      if (t < 1) requestAnimationFrame(raf);
    };
    requestAnimationFrame(raf);
  }, [clamped, animationDuration]);

  const displayOffset = circumference - (displayValue / 100) * circumference;

  return (
    <div
      className={`relative inline-flex ${pulse ? 'animate-pulse-slow' : ''} ${className}`}
      role="img"
      aria-label={ariaLabel ?? `Score: ${Math.round(value)} out of 100`}
    >
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
        aria-hidden="true"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={displayOffset}
          className="transition-[stroke-dashoffset] duration-300 ease-out"
          style={{ transitionDuration: `${animationDuration}ms` }}
        />
      </svg>
    </div>
  );
};

export default CircularProgressRing;
