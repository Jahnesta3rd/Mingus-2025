import { useEffect, useRef } from 'react';

interface StepShellProps {
  heading: string;
  description?: string;
  children: React.ReactNode;
}

export function StepShell({ heading, description, children }: StepShellProps) {
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    headingRef.current?.focus();
  }, [heading]);

  return (
    <section className="w-full max-w-[640px] rounded-xl border border-slate-200 bg-white p-4 sm:p-6">
      <h2 ref={headingRef} tabIndex={-1} className="text-2xl font-semibold text-slate-900 outline-none">
        {heading}
      </h2>
      {description && <p className="mt-2 text-sm text-slate-600">{description}</p>}
      <div className="mt-6">{children}</div>
    </section>
  );
}
