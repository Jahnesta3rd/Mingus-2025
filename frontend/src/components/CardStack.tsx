import React, { useRef } from 'react';

export interface CardStackProps {
  activeIndex: number;
  totalCards: number;
  onNext: () => void;
  onPrev: () => void;
  children: React.ReactNode;
  className?: string;
}

const PEEK_BANDS = [
  { top: -8, widthOffset: 28, height: 22, bg: '#2d1854', zIndex: 4 },
  { top: -16, widthOffset: 50, height: 20, bg: '#21133e', zIndex: 3 },
  { top: -24, widthOffset: 72, height: 18, bg: '#170a2c', zIndex: 2 },
  { top: -32, widthOffset: 94, height: 14, bg: '#0d061d', zIndex: 1 },
  { top: -38, widthOffset: 116, height: 8, bg: '#060210', zIndex: 0 },
] as const;

const CardStack: React.FC<CardStackProps> = ({
  activeIndex,
  totalCards,
  onNext,
  onPrev,
  children,
  className = '',
}) => {
  const touchStartX = useRef<number | null>(null);

  const jumpToIndex = (targetIndex: number) => {
    if (targetIndex === activeIndex) return;
    if (targetIndex > activeIndex) {
      for (let i = activeIndex; i < targetIndex; i += 1) {
        onNext();
      }
    } else {
      for (let i = activeIndex; i > targetIndex; i -= 1) {
        onPrev();
      }
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.changedTouches[0]?.clientX ?? null;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current === null) return;
    const endX = e.changedTouches[0]?.clientX ?? touchStartX.current;
    const deltaX = endX - touchStartX.current;
    touchStartX.current = null;

    if (deltaX < -40 && activeIndex < totalCards - 1) {
      onNext();
    } else if (deltaX > 40 && activeIndex > 0) {
      onPrev();
    }
  };

  return (
    <div className={className}>
      <div
        className="relative mx-auto w-full max-w-md"
        style={{ marginTop: 48, height: 484 }}
      >
        {PEEK_BANDS.map((band) => (
          <div
            key={band.zIndex}
            aria-hidden
            className="absolute"
            style={{
              top: band.top,
              left: '50%',
              transform: 'translateX(-50%)',
              width: `calc(100% - ${band.widthOffset}px)`,
              height: band.height,
              backgroundColor: band.bg,
              borderRadius: 22,
              zIndex: band.zIndex,
            }}
          />
        ))}

        <div
          className="relative h-full"
          style={{ zIndex: 5 }}
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          {children}
        </div>
      </div>

      <div
        className="mx-auto mt-4 flex items-center justify-center"
        style={{ gap: 6 }}
        role="tablist"
        aria-label="Dashboard cards"
      >
        {Array.from({ length: totalCards }, (_, index) => {
          const isActive = index === activeIndex;
          return (
            <button
              key={index}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-label={`Card ${index + 1} of ${totalCards}`}
              onClick={() => jumpToIndex(index)}
              className="border-0 bg-transparent p-0"
              style={{
                width: isActive ? 8 : 6,
                height: isActive ? 8 : 6,
                borderRadius: 999,
                backgroundColor: isActive ? '#5B2D8E' : '#c4b5fd',
                cursor: 'pointer',
              }}
            />
          );
        })}
      </div>
    </div>
  );
};

export default CardStack;
