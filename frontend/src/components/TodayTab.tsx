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
import ArticleRecommendationStrip from './ArticleRecommendationStrip';
import IndependenceCostCard from './IndependenceCostCard';
import MingusQuickSpend from './MingusQuickSpend';
import { useCardPriority } from '../hooks/useCardPriority';

export interface TodayTabProps {
  userEmail: string;
  userTier: 'budget' | 'mid_tier' | 'professional';
  initialCardIndex?: number;
  onCardChange?: (index: number) => void;
  onIndependencePurchaseClick?: () => void;
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

function CardStackSkeleton() {
  return (
    <div
      className="animate-pulse flex flex-col items-center justify-center"
      style={{
        minHeight: 280,
        borderRadius: 16,
        background: 'rgba(88,44,142,0.15)',
        padding: '32px 24px',
      }}
    >
      <div
        style={{
          width: '70%',
          height: 16,
          borderRadius: 4,
          background: 'rgba(88,44,142,0.25)',
          marginBottom: 12,
        }}
      />
      <div
        style={{
          width: '85%',
          height: 12,
          borderRadius: 4,
          background: 'rgba(88,44,142,0.25)',
          marginBottom: 12,
        }}
      />
      <div
        style={{
          width: '60%',
          height: 12,
          borderRadius: 4,
          background: 'rgba(88,44,142,0.25)',
        }}
      />
    </div>
  );
}

const TodayTab: React.FC<TodayTabProps> = ({
  userEmail,
  userTier,
  initialCardIndex,
  onCardChange,
  onIndependencePurchaseClick,
  className = '',
}) => {
  const navigate = useNavigate();
  const [activeIndex, setActiveIndex] = useState(initialCardIndex ?? 0);
  const { sortedCardIds, isReady } = useCardPriority(userEmail, userTier);

  const totalCards = sortedCardIds.length;
  const activeCardId = sortedCardIds[activeIndex] ?? sortedCardIds[0];
  const config =
    CARD_CONFIGS.find((c) => c.id === activeCardId) ??
    CARD_CONFIGS[activeIndex] ??
    CARD_CONFIGS[0];

  const eyebrowFor = (cardId: string): string => {
    const pos = sortedCardIds.indexOf(cardId) + 1;
    return `CARD ${pos} OF ${sortedCardIds.length}`;
  };

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
        {onIndependencePurchaseClick ? (
          <IndependenceCostCard
            onPurchaseClick={onIndependencePurchaseClick}
            className="mb-4"
          />
        ) : null}
        {!isReady ? (
          <CardStackSkeleton />
        ) : (
          <CardStack
            activeIndex={activeIndex}
            totalCards={totalCards}
            onNext={() =>
              handleIndexChange(Math.min(activeIndex + 1, totalCards - 1))
            }
            onPrev={() => handleIndexChange(Math.max(activeIndex - 1, 0))}
          >
            <HeroCard
              key={config.id}
              cardIndex={activeIndex}
              totalCards={totalCards}
              label={config.label}
              eyebrow={eyebrowFor(activeCardId)}
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
              {activeCardId === 'daily-outlook' && (
                <DailyOutlookCardBody userEmail={userEmail} userTier={userTier} />
              )}
              {activeCardId === 'vibe-roster' && (
                <VibeRosterCardBody userEmail={userEmail} userTier={userTier} />
              )}
              {activeCardId === 'cash-snapshot' && (
                <CashSnapshotCardBody userEmail={userEmail} userTier={userTier} />
              )}
              {activeCardId === 'career' && (
                <CareerCheckInCardBody userEmail={userEmail} userTier={userTier} />
              )}
              {activeCardId === 'vehicle' && (
                <VehicleCheckInCardBody userEmail={userEmail} userTier={userTier} />
              )}
              {activeCardId === 'housing' && (
                <HousingCheckInCardBody userEmail={userEmail} userTier={userTier} />
              )}
              {activeCardId === 'wellness' && (
                <WellnessCheckInCardBody userEmail={userEmail} userTier={userTier} />
              )}
            </HeroCard>
          </CardStack>
        )}
        <ArticleRecommendationStrip className="mt-4 px-4" />
      </div>
      <MingusQuickSpend />
    </div>
  );
};

export default TodayTab;
