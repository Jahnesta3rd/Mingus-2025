import { LandingPrimaryButton } from "../landing/LandingPrimaryButton";
import { LandingSection } from "../landing/LandingSection";

type Props = {
  onCta: () => void;
};

export function FinalCta({ onCta }: Props) {
  return (
    <LandingSection className="border-t border-[#2a2030] py-20 sm:py-28">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="font-display text-2xl font-semibold tracking-tight text-[#f0e8d8] sm:text-3xl">
          Your finances and your heart deserve clarity.
        </h2>
        <div className="mt-10 flex flex-col items-center gap-4">
          <LandingPrimaryButton type="button" onClick={onCta}>
            Start the Assessment
          </LandingPrimaryButton>
          <p className="text-sm text-[#9a8f7e]">
            Free to take. No credit card. No Mingus account needed.
          </p>
        </div>
      </div>
    </LandingSection>
  );
}
