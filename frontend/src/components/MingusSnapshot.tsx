import { useCallback, useEffect, useRef, useState } from 'react';
import type { ReactNode, TouchEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSnapshotData } from '../hooks/useSnapshotData';
import type { ActionData, FaithCardData, SnapshotData } from '../types/snapshot';

const TOTAL_CARDS = 3;
const SWIPE_THRESHOLD_PX = 50;

export interface MingusSnapshotProps {
  /** Called when user taps a CTA on the final action panel — receives the tab name to navigate to */
  onComplete: (topCta: string) => void;
  /** When set, the snapshot milestones card opens this instead of navigating via onComplete('milestones'). */
  onOpenAddImportantDate?: () => void;
  /** Bumping this refetches snapshot cards (e.g. after adding an important date). */
  snapshotReloadKey?: number;
}

function CardFrame({
  index,
  tag,
  title,
  showSwipeHint,
  swipeHintText,
  children,
}: {
  index: number;
  tag: string;
  title: string;
  showSwipeHint: boolean;
  /** When set with showSwipeHint, replaces default gray hint (purple styling). */
  swipeHintText?: string;
  children: ReactNode;
}) {
  return (
    <div
      className="box-border w-screen shrink-0 overflow-y-auto px-5 pb-[72px] pt-6"
      style={{ height: '100dvh', background: '#FAF5FF' }}
    >
      <p
        className="mb-2 text-[11px] font-medium uppercase tracking-wide"
        style={{ color: '#5B2D8E' }}
      >
        CARD {index} OF {TOTAL_CARDS} · {tag}
      </p>
      <h2 className="mb-4 text-[22px] font-bold" style={{ color: '#1E293B' }}>
        {title}
      </h2>
      {children}
      {showSwipeHint &&
        (swipeHintText ? (
          <p className="mt-10 text-center text-[12px]" style={{ color: '#5B2D8E' }}>
            {swipeHintText}
          </p>
        ) : (
          <p className="mt-10 text-center text-[12px] text-slate-500">Swipe to continue →</p>
        ))}
    </div>
  );
}

function DailySummaryDeckCard({
  loading,
  data,
}: {
  loading: boolean;
  data: SnapshotData;
}) {
  const signals = [
    { label: 'Vibe', value: data.vibe?.verdict ?? 'Check in' },
    { label: 'Cash', value: data.cash?.balance_status ?? 'Add balance' },
    { label: 'Career', value: data.career?.jobs?.[0]?.title ?? 'See matches' },
    {
      label: 'Roster',
      value: data.roster?.total_monthly_cost
        ? `$${data.roster.total_monthly_cost}/mo`
        : 'Add people',
    },
    { label: 'Housing', value: data.milestones?.upcoming?.[0]?.title ?? 'No events' },
  ];

  return (
    <div
      className="box-border w-screen shrink-0 overflow-y-auto px-5 pb-[72px] pt-6"
      style={{ height: '100dvh', background: '#FFFFFF' }}
    >
      <p
        className="mb-2 text-[11px] font-medium uppercase tracking-wide"
        style={{ color: '#5B2D8E' }}
      >
        CARD 2 OF {TOTAL_CARDS} · YOUR DAY AT A GLANCE
      </p>
      <h2 className="mb-4 text-[22px] font-bold" style={{ color: '#1E293B' }}>
        Your day at a glance
      </h2>
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="h-4 w-full max-w-md animate-pulse rounded bg-slate-200" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {signals.map(({ label, value }) => (
            <p key={label} className="text-[15px]" style={{ color: '#1E293B' }}>
              <span className="font-semibold">{label}:</span> {value}
            </p>
          ))}
        </div>
      )}
      <p className="mt-10 text-center text-[12px] text-slate-500">Swipe to continue →</p>
    </div>
  );
}

const URGENCY_RANK: Record<ActionData['ctas'][number]['urgency'], number> = {
  high: 0,
  medium: 1,
  low: 2,
};

function ActionTodayCardContent({
  loading,
  action,
}: {
  loading: boolean;
  action: ActionData | null;
}) {
  if (loading) {
    return (
      <div className="space-y-3 px-1">
        <div className="mx-auto h-6 w-32 animate-pulse rounded-full bg-slate-200" />
        <div className="mx-auto h-24 max-w-[280px] animate-pulse rounded-xl bg-slate-200" />
      </div>
    );
  }

  if (!action) {
    return (
      <div className="flex flex-col items-center px-2 pt-8 text-center">
        <p className="text-base font-semibold" style={{ color: '#1E293B' }}>
          Check back tomorrow.
        </p>
        <p className="mt-3 max-w-sm text-[15px] leading-relaxed text-slate-600">
          Your action will be ready once we have more data.
        </p>
      </div>
    );
  }

  const sourceLabel = action.action_source.replace(/-/g, '_').toUpperCase();

  return (
    <div className="flex flex-col items-center px-1 pt-2 text-center">
      <span
        className="inline-block rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide"
        style={{ backgroundColor: '#EDE9F6', color: '#5B2D8E' }}
      >
        {sourceLabel}
      </span>
      <p
        className="mx-auto my-6 max-w-[280px] text-center text-[20px] font-bold leading-[1.5]"
        style={{ color: '#1E293B' }}
      >
        {action.action_text}
      </p>
      <p className="text-[13px] text-slate-500">
        Based on what we found across your snapshot today.
      </p>
    </div>
  );
}

function FaithDeckCard({
  loading,
  faith,
  isFavorited,
  savedAnim,
  savedLabelOpacity,
  onFavoriteTap,
}: {
  loading: boolean;
  faith: FaithCardData | null;
  isFavorited: boolean;
  savedAnim: boolean;
  savedLabelOpacity: number;
  onFavoriteTap: () => void;
}) {
  const heartPath =
    'M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z';

  return (
    <div
      className="relative box-border flex w-screen shrink-0 flex-col overflow-y-auto px-5 pb-[72px] pt-6"
      style={{
        height: '100dvh',
        background: 'linear-gradient(160deg, #3b1f6e 0%, #5B2D8E 55%, #3b1f6e 100%)',
      }}
    >
      <p
        className="mb-2 text-[11px] font-medium uppercase"
        style={{ color: '#c4b5fd', letterSpacing: '0.2em' }}
      >
        CARD 1 OF {TOTAL_CARDS} · FAITH
      </p>

      <div className="flex min-h-0 flex-1 flex-col justify-center">
        {loading ? (
          <div className="flex flex-col items-center justify-center gap-3 py-8">
            <div
              className="h-3 w-[75%] max-w-sm animate-pulse rounded"
              style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}
            />
            <div
              className="h-3 w-[60%] max-w-xs animate-pulse rounded"
              style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}
            />
            <div
              className="h-3 w-[45%] max-w-[200px] animate-pulse rounded"
              style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}
            />
          </div>
        ) : !faith ? (
          <div className="flex flex-col items-center px-2 text-center">
            <span className="text-6xl" aria-hidden>
              🙏
            </span>
            <h3 className="mt-6 text-lg font-semibold" style={{ color: '#f5f3ff' }}>
              Start your day with the Word
            </h3>
            <p className="mt-3 max-w-sm text-[14px] leading-relaxed" style={{ color: '#ddd6fe' }}>
              We&apos;ll have a verse ready for you tomorrow.
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center px-2 py-4 text-center">
            <p
              className="mb-5 text-center text-[13px] font-medium uppercase"
              style={{
                color: '#fbbf24',
                letterSpacing: '0.12em',
              }}
            >
              {faith.verse_reference}
            </p>
            <p
              className="mx-auto max-w-[300px] text-center text-[20px] leading-[1.75]"
              style={{ color: '#f5f3ff', fontStyle: 'italic' }}
            >
              {faith.verse_text}
            </p>
            <div
              className="my-5 h-px w-10"
              style={{ backgroundColor: 'rgba(251,191,36,0.4)' }}
              aria-hidden
            />
            <p
              className="mx-auto max-w-[280px] text-center text-[14px] leading-[1.6]"
              style={{ color: '#ddd6fe' }}
            >
              {faith.bridge_sentence}
            </p>
          </div>
        )}
      </div>

      {faith && !loading ? (
        <div
          className="pointer-events-auto absolute flex items-center gap-2"
          style={{ bottom: 80, right: 24 }}
        >
          {savedAnim ? (
            <span
              style={{
                color: '#fbbf24',
                fontSize: 12,
                fontWeight: 500,
                opacity: savedLabelOpacity,
                transition: 'opacity 200ms ease',
              }}
            >
              Saved
            </span>
          ) : null}
          <button
            type="button"
            className="border-none bg-transparent p-0"
            aria-label={isFavorited ? 'Verse saved' : 'Save verse to favorites'}
            onClick={onFavoriteTap}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden>
              <path
                d={heartPath}
                fill={isFavorited ? '#fbbf24' : 'none'}
                stroke={isFavorited ? '#fbbf24' : 'rgba(255,255,255,0.5)'}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      ) : null}

      <p
        className="mt-10 shrink-0 text-center text-[12px]"
        style={{ color: 'rgba(196,181,253,0.8)' }}
      >
        Swipe to see your snapshot →
      </p>
    </div>
  );
}

function EndActionPanel({
  visible,
  action,
  onComplete,
}: {
  visible: boolean;
  action: ActionData | null;
  onComplete: (tab: string) => void;
}) {
  const sortedCtas = action?.ctas
    ? [...action.ctas].sort((a, b) => URGENCY_RANK[a.urgency] - URGENCY_RANK[b.urgency])
    : [];

  return (
    <div
      className="fixed bottom-0 left-0 right-0"
      style={{
        zIndex: 60,
        background: '#FFFFFF',
        borderTopLeftRadius: 24,
        borderTopRightRadius: 24,
        boxShadow: '0 -4px 24px rgba(0,0,0,0.10)',
        padding: '24px 20px 40px',
        transform: visible ? 'translateY(0)' : 'translateY(100%)',
        transition: 'transform 400ms cubic-bezier(0.4, 0, 0.2, 1)',
        pointerEvents: visible ? 'auto' : 'none',
      }}
    >
      <div
        className="mx-auto mb-4 rounded-full bg-slate-300"
        style={{ width: 40, height: 4 }}
        aria-hidden
      />
      <h3 className="text-[18px] font-bold" style={{ color: '#1E293B' }}>
        Your next steps
      </h3>
      <p className="mb-4 mt-1 text-[13px] text-slate-500">Based on your snapshot</p>
      {sortedCtas.map((cta) => {
        const high = cta.urgency === 'high';
        const medium = cta.urgency === 'medium';
        return (
          <div
            key={`${cta.tab}-${cta.label}`}
            role="button"
            tabIndex={visible ? 0 : -1}
            className="mb-2 cursor-pointer rounded-xl p-4 text-[15px] font-bold"
            style={
              high
                ? { backgroundColor: '#5B2D8E', color: '#FFFFFF' }
                : medium
                  ? {
                      backgroundColor: '#FFFFFF',
                      border: '1.5px solid #5B2D8E',
                      color: '#5B2D8E',
                    }
                  : {
                      backgroundColor: '#FFFFFF',
                      border: '1.5px solid #E2E8F0',
                      color: '#64748B',
                    }
            }
            onClick={() => onComplete(cta.tab)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onComplete(cta.tab);
              }
            }}
          >
            {cta.label}
          </div>
        );
      })}
      <div
        role="button"
        tabIndex={visible ? 0 : -1}
        className="mt-3 cursor-pointer text-center text-[13px] text-slate-500"
        onClick={() => onComplete('dashboard')}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onComplete('dashboard');
          }
        }}
      >
        Skip — take me to my dashboard
      </div>
    </div>
  );
}

function MingusSnapshot({
  onComplete,
  onOpenAddImportantDate,
  snapshotReloadKey = 0,
}: MingusSnapshotProps) {
  const navigate = useNavigate();
  const { data, loadStates, saveFavorite } = useSnapshotData({
    reloadKey: snapshotReloadKey,
  });
  const [index, setIndex] = useState(0);
  const [endPanelVisible, setEndPanelVisible] = useState(false);
  const [savedAnim, setSavedAnim] = useState(false);
  const [savedLabelOpacity, setSavedLabelOpacity] = useState(0);
  const [isFavorited, setIsFavorited] = useState(false);
  const touchStartXRef = useRef<number | null>(null);

  useEffect(() => {
    setIsFavorited(Boolean(data.faith?.is_favorited));
  }, [data.faith]);

  useEffect(() => {
    if (!savedAnim) return;
    setSavedLabelOpacity(0);
    let rafInner = 0;
    const rafOuter = requestAnimationFrame(() => {
      rafInner = requestAnimationFrame(() => setSavedLabelOpacity(1));
    });
    const tFadeOut = window.setTimeout(() => setSavedLabelOpacity(0), 1200);
    const tClear = window.setTimeout(() => {
      setSavedAnim(false);
      setSavedLabelOpacity(0);
    }, 1500);
    return () => {
      cancelAnimationFrame(rafOuter);
      cancelAnimationFrame(rafInner);
      window.clearTimeout(tFadeOut);
      window.clearTimeout(tClear);
    };
  }, [savedAnim]);

  useEffect(() => {
    if (index !== 2) {
      setEndPanelVisible(false);
      return;
    }
    const t = window.setTimeout(() => setEndPanelVisible(true), 600);
    return () => window.clearTimeout(t);
  }, [index]);

  const onTouchStart = useCallback((e: TouchEvent) => {
    touchStartXRef.current = e.changedTouches[0]?.clientX ?? e.touches[0]?.clientX ?? null;
  }, []);

  const onTouchEnd = useCallback(
    (e: TouchEvent) => {
      const startX = touchStartXRef.current;
      touchStartXRef.current = null;
      if (startX == null) return;
      const endX = e.changedTouches[0]?.clientX;
      if (endX == null) return;
      const delta = endX - startX;
      setIndex((i) => {
        if (delta < -SWIPE_THRESHOLD_PX && i < TOTAL_CARDS - 1) return i + 1;
        if (delta > SWIPE_THRESHOLD_PX && i > 0) return i - 1;
        return i;
      });
    },
    [],
  );

  const handleFaithFavoriteTap = useCallback(() => {
    if (isFavorited || !data.faith) return;
    setIsFavorited(true);
    setSavedAnim(true);
    void saveFavorite(data.faith).then((ok) => {
      if (!ok) setIsFavorited(false);
    });
  }, [isFavorited, data.faith, saveFavorite]);

  const handleCloseSnapshot = useCallback(() => {
    if (
      window.confirm(
        'Leave this summary and go to your dashboard? You can open it again from the app when you are ready.',
      )
    ) {
      navigate('/dashboard');
    }
  }, [navigate]);

  const faithLoading = loadStates.faith === 'loading';
  const dailySummaryLoading =
    loadStates.vibe === 'loading' ||
    loadStates.cash === 'loading' ||
    loadStates.career === 'loading' ||
    loadStates.roster === 'loading' ||
    loadStates.milestones === 'loading';
  const actionLoading = loadStates.action === 'loading';

  return (
    <>
      <button
        type="button"
        onClick={handleCloseSnapshot}
        className="fixed right-3 top-[max(0.75rem,env(safe-area-inset-top))] z-[70] flex h-11 w-11 min-h-[44px] min-w-[44px] items-center justify-center rounded-full border border-slate-300 bg-white/95 text-lg font-light leading-none text-slate-700 shadow-sm hover:bg-white hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
        aria-label="Close snapshot and go to dashboard"
      >
        <span aria-hidden>×</span>
      </button>
      <div
        className="fixed left-0 top-0 z-50 overflow-hidden bg-[#F8FAFC]"
        style={{ width: '100vw', height: '100dvh' }}
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
      >
        <div
          className="flex flex-row"
          style={{
            width: `calc(100vw * ${TOTAL_CARDS})`,
            transform: `translateX(-${index * 100}vw)`,
            transition: 'transform 350ms cubic-bezier(0.4, 0, 0.2, 1)',
            willChange: 'transform',
          }}
        >
          <FaithDeckCard
            loading={faithLoading}
            faith={data.faith}
            isFavorited={isFavorited}
            savedAnim={savedAnim}
            savedLabelOpacity={savedLabelOpacity}
            onFavoriteTap={handleFaithFavoriteTap}
          />

          <DailySummaryDeckCard loading={dailySummaryLoading} data={data} />

          <CardFrame
            index={3}
            tag="ONE THING TO DO TODAY"
            title="One thing to do today"
            showSwipeHint
            swipeHintText="Swipe to see your next steps →"
          >
            <ActionTodayCardContent loading={actionLoading} action={data.action} />
          </CardFrame>
        </div>
      </div>

      <EndActionPanel
        visible={endPanelVisible && index === 2}
        action={data.action}
        onComplete={onComplete}
      />

      <div
        className="fixed bottom-6 left-0 right-0 z-[60] flex justify-center gap-2"
      >
        {Array.from({ length: TOTAL_CARDS }, (_, i) => (
          <button
            key={i}
            type="button"
            aria-label={`Go to card ${i + 1}`}
            aria-current={i === index ? 'true' : undefined}
            onClick={() => setIndex(i)}
            className="block h-2 w-2 rounded-full cursor-pointer"
            style={{
              backgroundColor: i === index ? '#5B2D8E' : '#CBD5E1',
              border: 'none',
              padding: 0,
            }}
          />
        ))}
      </div>
    </>
  );
}

export default MingusSnapshot;
