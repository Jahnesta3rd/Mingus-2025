import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CardStack from './CardStack';
import HeroCard from './HeroCard';
import CashSnapshotCardBody from './CashSnapshotCardBody';
import CareerCheckInCardBody from './CareerCheckInCardBody';
import DailyOutlookCardBody from './DailyOutlookCardBody';
import VibeRosterCardBody from './VibeRosterCardBody';
import VehicleCheckInCardBody from './VehicleCheckInCardBody';
import HousingCheckInCardBody from './HousingCheckInCardBody';
import WellnessCheckInCardBody from './WellnessCheckInCardBody';
import { CARD_CONFIGS } from './cardConfigs';

export interface TodayTabProps {
  userEmail: string;
  userTier: 'budget' | 'mid_tier' | 'professional';
  initialCardIndex?: number;
  onCardChange?: (index: number) => void;
  className?: string;
}

function getTimeOfDay(): 'morning' | 'afternoon' | 'evening' {
  const hour = new Date().getHours();
  if (hour < 12) return 'morning';
  if (hour < 17) return 'afternoon';
  return 'evening';
}

function greetingNameFromEmail(email: string): string {
  if (!email.trim()) return 'there';
  const local = email.split('@')[0] ?? '';
  const segment = local.split(/[._+-]/)[0] ?? '';
  if (!segment) return 'there';
  return segment.charAt(0).toUpperCase() + segment.slice(1).toLowerCase();
}

function CardIcon({ path }: { path: string }) {
  return (
    <svg
      width={18}
      height={18}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ color: '#f5f3ff' }}
      aria-hidden
    >
      <path d={path} />
    </svg>
  );
}

const TOTAL_CARDS = CARD_CONFIGS.length;

const TodayTab: React.FC<TodayTabProps> = ({
  userEmail,
  userTier,
  initialCardIndex,
  onCardChange,
  className = '',
}) => {
  const navigate = useNavigate();
  const [activeIndex, setActiveIndex] = useState(initialCardIndex ?? 0);
  const config = CARD_CONFIGS[activeIndex];

  const handleIndexChange = (index: number) => {
    setActiveIndex(index);
    onCardChange?.(index);
  };

  return (
    <div
      className={className}
      style={{ backgroundColor: '#FAF5FF', paddingBottom: 80 }}
    >
      <h1
        style={{
          fontSize: 20,
          fontWeight: 700,
          color: '#1A1815',
          padding: '16px 16px 8px',
          margin: 0,
        }}
      >
        Good {getTimeOfDay()}, {greetingNameFromEmail(userEmail)}
      </h1>

      <div style={{ padding: '0 16px' }}>
        <CardStack
          activeIndex={activeIndex}
          totalCards={TOTAL_CARDS}
          onNext={() =>
            handleIndexChange(Math.min(activeIndex + 1, TOTAL_CARDS - 1))
          }
          onPrev={() => handleIndexChange(Math.max(activeIndex - 1, 0))}
        >
          <HeroCard
            key={config.id}
            cardIndex={activeIndex}
            totalCards={TOTAL_CARDS}
            label={config.label}
            eyebrow={config.eyebrow}
            backgroundColor={config.backgroundColor}
            accentColor={config.accentColor}
            icon={<CardIcon path={config.iconPath} />}
            onTap={() =>
              navigate(
                config.drillRoute.includes('?')
                  ? config.drillRoute + '&from=today&card=' + activeIndex
                  : config.drillRoute + '?from=today&card=' + activeIndex
              )
            }
          >
            {activeIndex === 0 ? (
              <DailyOutlookCardBody userEmail={userEmail} userTier={userTier} />
            ) : activeIndex === 1 ? (
              <VibeRosterCardBody userEmail={userEmail} userTier={userTier} />
            ) : activeIndex === 2 ? (
              <CashSnapshotCardBody userEmail={userEmail} userTier={userTier} />
            ) : activeIndex === 3 ? (
              <CareerCheckInCardBody userEmail={userEmail} userTier={userTier} />
            ) : activeIndex === 4 ? (
              <VehicleCheckInCardBody userEmail={userEmail} userTier={userTier} />
            ) : activeIndex === 5 ? (
              <HousingCheckInCardBody userEmail={userEmail} userTier={userTier} />
            ) : activeIndex === 6 ? (
              <WellnessCheckInCardBody userEmail={userEmail} userTier={userTier} />
            ) : (
              <p
                className="text-center"
                style={{
                  fontSize: 13,
                  color: 'rgba(255,255,255,0.6)',
                  margin: 0,
                }}
              >
                {config.placeholder}
              </p>
            )}
          </HeroCard>
        </CardStack>
      </div>
    </div>
  );
};

export default TodayTab;
