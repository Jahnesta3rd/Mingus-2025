import type { CSSProperties } from "react";
import { LandingPrimaryButton } from "../landing/LandingPrimaryButton";
import { LandingSection } from "../landing/LandingSection";

const SUBHEAD =
  "25 questions. Real talk. Find out if the person you're into is an emotional asset or a financial liability — and what the next 12 months could actually cost you.";

const heroMeshStyle: CSSProperties = {
  backgroundImage: `
    radial-gradient(ellipse 120% 80% at 50% -20%, rgba(196, 160, 100, 0.14), transparent 55%),
    radial-gradient(ellipse 70% 50% at 100% 40%, rgba(196, 160, 100, 0.07), transparent 50%),
    radial-gradient(ellipse 60% 45% at 0% 80%, rgba(196, 160, 100, 0.06), transparent 50%)
  `,
};

type Props = {
  onPrimaryCta: () => void;
};

export function LandingHero({ onPrimaryCta }: Props) {
  return (
    <div className="relative overflow-hidden bg-[#0d0a08]" style={heroMeshStyle}>
      <div className="landing-grain" aria-hidden />
      <LandingSection className="relative py-20 sm:py-28 lg:py-36">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="font-display text-[clamp(2rem,6vw,3.5rem)] font-semibold leading-[1.12] tracking-tight text-[#f0e8d8] min-h-[8.5rem] sm:min-h-[10rem] lg:min-h-[11rem]">
            Is This Person{" "}
            <span className="text-[#C4A064] italic">Worth Your Vibe?</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-[#9a8f7e] sm:text-lg">
            {SUBHEAD}
          </p>
          <div className="mt-10 flex flex-col items-center gap-4">
            <LandingPrimaryButton type="button" onClick={onPrimaryCta}>
              Find Out Now — It&apos;s Free
            </LandingPrimaryButton>
            <p className="text-sm text-[#9a8f7e]">
              Takes ~6 minutes · No account required · Used by 1,000+ people
            </p>
          </div>
        </div>
      </LandingSection>
    </div>
  );
}
