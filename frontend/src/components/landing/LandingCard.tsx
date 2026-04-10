import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
};

export function LandingCard({ children, className = "" }: Props) {
  return (
    <div
      className={`rounded-2xl border border-[#2a2030] bg-[#1a1520]/80 p-6 shadow-landing-card backdrop-blur-sm sm:p-7 ${className}`}
    >
      {children}
    </div>
  );
}
