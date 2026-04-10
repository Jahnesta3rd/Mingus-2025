import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
  id?: string;
};

export function LandingSection({ children, className = "", id }: Props) {
  return (
    <section
      id={id}
      className={`mx-auto w-full max-w-6xl px-5 sm:px-6 lg:px-8 ${className}`}
    >
      {children}
    </section>
  );
}
