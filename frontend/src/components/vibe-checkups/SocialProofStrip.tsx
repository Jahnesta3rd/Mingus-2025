import { LandingCard } from "../landing/LandingCard";
import { LandingSection } from "../landing/LandingSection";

const CARDS = [
  {
    emoji: "🔥",
    verdict: "Run. Just Run.",
    quote: "I knew something was off. This confirmed it.",
  },
  {
    emoji: "🌿",
    verdict: "Green Flag Royalty",
    quote: "Finally put into words what I felt about him.",
  },
  {
    emoji: "🚩",
    verdict: "Red Flag Parade",
    quote: "The 12-month number made me reconsider everything.",
  },
] as const;

export function SocialProofStrip() {
  return (
    <LandingSection className="py-16 sm:py-20">
      <div className="grid gap-5 sm:grid-cols-3">
        {CARDS.map((c) => (
          <LandingCard key={c.verdict} className="flex flex-col gap-3 text-left">
            <div className="flex items-center gap-2">
              <span className="text-2xl" aria-hidden>
                {c.emoji}
              </span>
              <span className="font-display text-lg font-semibold text-[#f0e8d8]">
                {c.verdict}
              </span>
            </div>
            <p className="text-sm leading-relaxed text-[#9a8f7e]">&ldquo;{c.quote}&rdquo;</p>
          </LandingCard>
        ))}
      </div>
    </LandingSection>
  );
}
