import type { ReactNode } from 'react';

export type RosterSectionProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  /** Override default label color (#9CA3AF), e.g. inner-circle muted purple on dark. */
  titleClassName?: string;
};

export function RosterSection({ title, subtitle, children, titleClassName }: RosterSectionProps) {
  const labelColor = titleClassName ?? 'text-[#9CA3AF]';
  return (
    <section>
      <div className={`text-[11px] font-medium uppercase tracking-[0.1em] ${labelColor}`}>{title}</div>
      {subtitle ? <p className="mt-1 text-sm text-[#9a8f7e]">{subtitle}</p> : null}
      <div className="mt-3 h-px w-full bg-[#2a2030]" aria-hidden />
      <div className="mt-4">{children}</div>
    </section>
  );
}
