import { useEffect, useMemo } from 'react';
import { CARD_CONFIGS } from '../components/cardConfigs';
import { useDailyOutlookCache } from './useDailyOutlookCache';
import { useVibeTracker } from './useVibeTracker';
import { useLifeLedger } from './useLifeLedger';
import { useCashForecast } from './useCashForecast';
import { useCareerCheckIn } from './useCareerCheckIn';
import { useVehicleDashboard } from './useVehicleDashboard';
import { useHousingCheckIn } from './useHousingCheckIn';
import { useWellnessData } from './useWellnessData';

const DAILY_OUTLOOK_ID = 'daily-outlook';
const SCORABLE_CARD_IDS = CARD_CONFIGS.filter((c) => c.id !== DAILY_OUTLOOK_ID).map(
  (c) => c.id
);
const ORIGINAL_ORDER_BY_ID = new Map(
  CARD_CONFIGS.map((c) => [c.id, c.originalOrder] as const)
);
const DEFAULT_SORTED_IDS = CARD_CONFIGS.map((c) => c.id);

export interface CardData {
  dailyOutlook: ReturnType<typeof useDailyOutlookCache>;
  vibeRoster: {
    tracker: ReturnType<typeof useVibeTracker>;
    lifeLedger: ReturnType<typeof useLifeLedger>;
  };
  cash: ReturnType<typeof useCashForecast>;
  career: ReturnType<typeof useCareerCheckIn>;
  vehicle: ReturnType<typeof useVehicleDashboard>;
  housing: ReturnType<typeof useHousingCheckIn>;
  wellness: ReturnType<typeof useWellnessData>;
}

export interface UseCardPriorityResult {
  sortedCardIds: string[];
  cardData: CardData;
  isReady: boolean;
}

function capScore(score: number): number {
  return Math.min(score, 80);
}

function isAssessedStale(lastAssessedAt: string | null): boolean {
  if (!lastAssessedAt) return true;
  const fourteenDaysMs = 14 * 24 * 60 * 60 * 1000;
  return Date.now() - new Date(lastAssessedAt).getTime() > fourteenDaysMs;
}

function scoreVibeRoster(tracker: ReturnType<typeof useVibeTracker>): number {
  const activePeople = (tracker.data ?? []).filter((p) => !p.is_archived);
  let score = 0;

  const decliningCount = activePeople.filter(
    (p) => p.trend?.trend_direction === 'declining'
  ).length;
  score += Math.min(decliningCount * 40, 80);

  if (activePeople.some((p) => isAssessedStale(p.last_assessed_at))) {
    score += 30;
  }

  return capScore(score);
}

function scoreCash(cash: ReturnType<typeof useCashForecast>): number {
  const data = cash.data;
  if (!data) return 0;

  let score = 0;
  if (data.balanceStatus === 'danger') score += 70;
  else if (data.balanceStatus === 'warning') score += 40;
  if (data.netChange < -500) score += 20;

  return capScore(score);
}

function scoreCareer(
  career: ReturnType<typeof useCareerCheckIn>,
  userTier: 'budget' | 'mid_tier' | 'professional'
): number {
  if (userTier === 'budget') return 0;

  const data = career.data;
  if (!data) return 0;

  let score = 0;
  if (!data.profileComplete) score += 25;
  if (data.openToMove) score += 20;

  return capScore(score);
}

function scoreVehicle(vehicle: ReturnType<typeof useVehicleDashboard>): number {
  const data = vehicle.data;
  if (!data || !data.hasVehicles) return 0;

  let score = 0;
  if (data.overdueMaintenanceCount > 0) {
    score += Math.min(data.overdueMaintenanceCount * 50, 80);
  }
  if (data.upcomingMaintenanceCount > 0) score += 20;

  return capScore(score);
}

function scoreHousing(housing: ReturnType<typeof useHousingCheckIn>): number {
  const data = housing.data;
  if (!data) return 0;

  let score = 0;
  if (
    data.hasBuyGoal &&
    data.targetTimelineMonths != null &&
    data.targetTimelineMonths < 6
  ) {
    score += 50;
  }
  if (data.hasBuyGoal) score += 20;
  if (!data.profileComplete) score += 15;

  return capScore(score);
}

function scoreWellness(wellness: ReturnType<typeof useWellnessData>): number {
  let score = 0;

  if (wellness.weeksOfData === 0) score += 30;

  const overall = wellness.scores?.overall_wellness_score;
  if (
    wellness.hasRealScores &&
    overall != null &&
    overall < 50
  ) {
    score += 25;
  }

  if (!wellness.streak || wellness.streak.current_streak === 0) {
    score += 15;
  }

  return capScore(score);
}

function scoreForCardId(
  cardId: string,
  cardData: CardData,
  userTier: 'budget' | 'mid_tier' | 'professional'
): number {
  switch (cardId) {
    case 'vibe-roster':
      return scoreVibeRoster(cardData.vibeRoster.tracker);
    case 'cash-snapshot':
      return scoreCash(cardData.cash);
    case 'career':
      return scoreCareer(cardData.career, userTier);
    case 'vehicle':
      return scoreVehicle(cardData.vehicle);
    case 'housing':
      return scoreHousing(cardData.housing);
    case 'wellness':
      return scoreWellness(cardData.wellness);
    default:
      return 0;
  }
}

function isVibeRosterLoading(cardData: CardData): boolean {
  return (
    cardData.vibeRoster.tracker.loading || cardData.vibeRoster.lifeLedger.loading
  );
}

function countResolvedScorableHooks(cardData: CardData): number {
  let resolved = 0;
  if (!isVibeRosterLoading(cardData)) resolved += 1;
  if (!cardData.cash.loading) resolved += 1;
  if (!cardData.career.loading) resolved += 1;
  if (!cardData.vehicle.loading) resolved += 1;
  if (!cardData.housing.loading) resolved += 1;
  if (!cardData.wellness.loading) resolved += 1;
  return resolved;
}

function allScorableHooksLoading(cardData: CardData): boolean {
  return countResolvedScorableHooks(cardData) === 0;
}

export function useCardPriority(
  userEmail: string,
  userTier: 'budget' | 'mid_tier' | 'professional'
): UseCardPriorityResult {
  const dailyOutlook = useDailyOutlookCache();
  const tracker = useVibeTracker();
  const lifeLedger = useLifeLedger(true);
  const cash = useCashForecast(userEmail);
  const career = useCareerCheckIn(userEmail, userTier);
  const vehicle = useVehicleDashboard();
  const housing = useHousingCheckIn();
  const wellness = useWellnessData();

  useEffect(() => {
    void tracker.getPeople().catch(() => {
      /* error surfaced via hook */
    });
  }, [tracker.getPeople]);

  const cardData: CardData = useMemo(
    () => ({
      dailyOutlook,
      vibeRoster: { tracker, lifeLedger },
      cash,
      career,
      vehicle,
      housing,
      wellness,
    }),
    [dailyOutlook, tracker, lifeLedger, cash, career, vehicle, housing, wellness]
  );

  const isReady = countResolvedScorableHooks(cardData) >= 3;

  const sortedCardIds = useMemo(() => {
    if (allScorableHooksLoading(cardData)) {
      return DEFAULT_SORTED_IDS;
    }

    const scored = SCORABLE_CARD_IDS.map((id) => ({
      id,
      score: scoreForCardId(id, cardData, userTier),
      originalOrder: ORIGINAL_ORDER_BY_ID.get(id) ?? 0,
    }));

    scored.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.originalOrder - b.originalOrder;
    });

    return [DAILY_OUTLOOK_ID, ...scored.map((entry) => entry.id)];
  }, [cardData, userTier]);

  return { sortedCardIds, cardData, isReady };
}
