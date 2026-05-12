import React, { useEffect, useRef, useState } from 'react';
import { Check, X } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

interface PricingTier {
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  popular?: boolean;
  cta: string;
}

interface PricingSectionProps {
  pricingTiers: PricingTier[];
  navigate: (path: string) => void;
}

const TIER_ORDER: Record<'budget' | 'mid_tier' | 'professional', number> = {
  budget: 1,
  mid_tier: 2,
  professional: 3,
};

const PLACEHOLDER_MESSAGE =
  'Self-service upgrades are coming soon. Email support@mingus.app to upgrade your plan.';

function normalizeTierName(name: string): 'budget' | 'mid_tier' | 'professional' | null {
  const k = name.trim().toLowerCase().replace(/-/g, '_').replace(/\s+/g, '_');
  if (k === 'budget' || k === 'mid_tier' || k === 'professional') {
    return k;
  }
  return null;
}

type CardCtaState = 'signup' | 'current' | 'upgrade' | 'downgrade';

function getCardState(
  isAuthenticated: boolean,
  userTier: 'budget' | 'mid_tier' | 'professional' | null,
  tierKey: 'budget' | 'mid_tier' | 'professional' | null
): CardCtaState {
  if (!isAuthenticated || userTier === null || tierKey === null) {
    return 'signup';
  }
  if (tierKey === userTier) return 'current';
  if (TIER_ORDER[tierKey] > TIER_ORDER[userTier]) return 'upgrade';
  return 'downgrade';
}

const PricingSection: React.FC<PricingSectionProps> = ({ pricingTiers, navigate }) => {
  const { isAuthenticated, userTier } = useAuth();
  const [showPlaceholderMessage, setShowPlaceholderMessage] = useState(false);
  const messageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!showPlaceholderMessage) return;
    const handlePointerDown = (event: MouseEvent | TouchEvent) => {
      const target = event.target as Node;
      if (messageRef.current && !messageRef.current.contains(target)) {
        setShowPlaceholderMessage(false);
      }
    };
    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('touchstart', handlePointerDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('touchstart', handlePointerDown);
    };
  }, [showPlaceholderMessage]);

  const openPlaceholderMessage = () => {
    setShowPlaceholderMessage(true);
  };

  const baseButtonClass =
    'w-full min-h-[44px] px-6 rounded-lg font-semibold transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-gray-800 flex items-center justify-center';

  return (
    <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-800/50" role="region" aria-label="Pricing plans">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            {isAuthenticated ? 'Upgrade your plan' : 'Choose Your Plan'}
          </h2>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Paid plans from day one — pick the tier that fits you. All plans include our core features.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {pricingTiers.map((tier, index) => {
            const tierKey = normalizeTierName(tier.name);
            const state = getCardState(isAuthenticated, userTier, tierKey);

            const slug = tier.name.toLowerCase().replace(/\s+/g, '-');

            const signupPrimaryClass =
              'bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white shadow-lg hover:shadow-violet-500/25 transform hover:scale-105';
            const signupOutlineClass =
              'border-2 border-violet-500 text-violet-400 hover:bg-violet-500 hover:text-white hover:shadow-lg hover:shadow-violet-500/25 transform hover:scale-105';

            const currentClass =
              'cursor-not-allowed border-2 border-gray-600 bg-gray-700/80 text-gray-400 opacity-80';

            const upgradeClass =
              'bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white shadow-lg hover:shadow-violet-500/25 transform hover:scale-105';

            const downgradeClass =
              'border-2 border-gray-500 text-gray-300 hover:bg-gray-700 hover:text-white transform hover:scale-105';

            let buttonClass = baseButtonClass;
            let label = tier.cta;
            let ariaLabel = `Subscribe to ${tier.name} plan for ${tier.price} per ${tier.period}`;
            let onClick: (() => void) | undefined = () => navigate('/signup?source=cta');
            let disabled = false;
            let ariaDisabled: boolean | undefined;

            if (state === 'signup') {
              buttonClass += ` ${tier.popular ? signupPrimaryClass : signupOutlineClass}`;
            } else if (state === 'current') {
              buttonClass += ` ${currentClass}`;
              label = 'Current Plan';
              ariaLabel = `Current plan: ${tier.name}`;
              onClick = undefined;
              disabled = true;
              ariaDisabled = true;
            } else if (state === 'upgrade') {
              buttonClass += ` ${upgradeClass}`;
              label = `Upgrade to ${tier.name}`;
              ariaLabel = `Upgrade to ${tier.name} plan`;
              onClick = openPlaceholderMessage;
            } else {
              buttonClass += ` ${downgradeClass}`;
              label = `Switch to ${tier.name}`;
              ariaLabel = `Switch to ${tier.name} plan`;
              onClick = openPlaceholderMessage;
            }

            return (
              <div
                key={index}
                className={`group bg-gray-800 p-8 rounded-xl relative transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-violet-500/20 hover:-translate-y-2 ${tier.popular ? 'ring-2 ring-violet-500 hover:ring-violet-400' : 'hover:ring-2 hover:ring-violet-500/50'}`}
              >
                {tier.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-gradient-to-r from-violet-500 to-purple-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                      Most Popular
                    </span>
                  </div>
                )}
                <div className="text-center mb-6">
                  <h2 className="text-2xl font-bold mb-2 text-white group-hover:text-violet-100 transition-colors duration-300">
                    {tier.name}
                  </h2>
                  <div className="mb-2">
                    <span className="text-4xl font-bold text-violet-400 group-hover:text-violet-300 transition-colors duration-300">
                      {tier.price}
                    </span>
                    <span className="text-gray-400 group-hover:text-gray-300 transition-colors duration-300">
                      /{tier.period}
                    </span>
                  </div>
                  <p className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300">{tier.description}</p>
                </div>
                <ul className="space-y-3 mb-8" id={`${slug}-features`}>
                  {tier.features.map((feature, featureIndex) => (
                    <li
                      key={featureIndex}
                      className="flex items-start group-hover:translate-x-1 transition-transform duration-300"
                      style={{ transitionDelay: `${featureIndex * 50}ms` }}
                    >
                      <Check className="w-5 h-5 text-violet-400 mt-0.5 mr-3 flex-shrink-0 group-hover:text-violet-300 transition-colors duration-300" aria-hidden="true" />
                      <span className="text-gray-300 group-hover:text-gray-200 transition-colors duration-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                <div id={`${slug}-description`} className="sr-only">
                  {tier.description}. Features include: {tier.features.join(', ')}
                </div>
                <button
                  type="button"
                  className={buttonClass}
                  aria-label={ariaLabel}
                  aria-describedby={`${slug}-description ${slug}-features`}
                  aria-disabled={ariaDisabled}
                  disabled={disabled}
                  onClick={onClick}
                >
                  {label}
                </button>
              </div>
            );
          })}
        </div>

        {showPlaceholderMessage && (
          <div ref={messageRef} className="mt-8 max-w-2xl mx-auto rounded-lg border border-slate-600 bg-slate-900/90 px-4 py-3 text-left text-sm text-gray-300 shadow-lg sm:px-5 sm:text-base">
            <div className="flex gap-3">
              <p className="min-w-0 flex-1 leading-relaxed">{PLACEHOLDER_MESSAGE}</p>
              <button
                type="button"
                className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-md text-gray-400 transition-colors hover:bg-slate-800 hover:text-white focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-slate-900"
                aria-label="Dismiss message"
                onClick={() => setShowPlaceholderMessage(false)}
              >
                <X className="h-5 w-5" aria-hidden />
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

export default PricingSection;
