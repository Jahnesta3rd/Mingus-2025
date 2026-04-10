import React from 'react';

export interface InsightCardProps {
  icon: string;
  title: string;
  body: string;
  accentColor?: string;
}

const DEFAULT_ACCENT = '#C4A064';

export const InsightCard: React.FC<InsightCardProps> = ({
  icon,
  title,
  body,
  accentColor = DEFAULT_ACCENT,
}) => {
  return (
    <div
      className="relative overflow-hidden rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
      style={{ borderLeftWidth: 4, borderLeftColor: accentColor }}
    >
      <div className="text-4xl leading-none" aria-hidden>
        {icon}
      </div>
      <h3 className="mt-3 text-base font-bold text-[#0f172a]">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">{body}</p>
    </div>
  );
};
