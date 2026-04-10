import { LandingSection } from "../landing/LandingSection";

const STEPS = [
  {
    title: "Answer honestly",
    body: "Answer 25 honest questions about your person",
    icon: (
      <svg className="h-8 w-8" viewBox="0 0 32 32" fill="none" aria-hidden>
        <circle cx="16" cy="11" r="4" stroke="currentColor" strokeWidth="1.5" />
        <path
          d="M8 26c0-4.4 3.6-8 8-8s8 3.6 8 8"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
    ),
  },
  {
    title: "Get your scores",
    body: "Get your Emotional Match and Financial Match scores",
    icon: (
      <svg className="h-8 w-8" viewBox="0 0 32 32" fill="none" aria-hidden>
        <path
          d="M6 22V10M12 22V6M18 22v-8M24 22V14"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
    ),
  },
  {
    title: "See the projection",
    body: "See your personalized 12-month financial projection",
    icon: (
      <svg className="h-8 w-8" viewBox="0 0 32 32" fill="none" aria-hidden>
        <path
          d="M6 24h20M8 20l4-6 4 5 4-10 4 7"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
] as const;

export function HowItWorks() {
  return (
    <LandingSection className="border-t border-[#2a2030] py-16 sm:py-24">
      <h2 className="font-display text-center text-2xl font-semibold tracking-tight text-[#f0e8d8] sm:text-3xl">
        How it works
      </h2>
      <div className="mt-12 flex flex-col gap-10 md:flex-row md:gap-8 lg:gap-12">
        {STEPS.map((s, i) => (
          <div
            key={s.title}
            className="flex flex-1 flex-col items-center text-center md:items-start md:text-left"
          >
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#C4A064]/12 text-[#C4A064]">
              {s.icon}
            </div>
            <p className="mt-1 font-display text-sm font-medium text-[#C4A064]">
              Step {i + 1}
            </p>
            <h3 className="mt-2 font-display text-lg font-semibold text-[#f0e8d8]">{s.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-[#9a8f7e]">{s.body}</p>
          </div>
        ))}
      </div>
    </LandingSection>
  );
}
