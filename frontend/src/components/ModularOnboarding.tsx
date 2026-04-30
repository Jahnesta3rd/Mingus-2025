import { useEffect, useRef } from 'react';
import { useModularOnboarding } from '../hooks/useModularOnboarding';
import { OnboardingCanvas } from './OnboardingCanvas';
import { InputBar } from './chat/InputBar';
import { MessageBubble } from './chat/MessageBubble';
import { TypingIndicator } from './chat/TypingIndicator';

/** Pixels from the bottom of the message list to treat as "following" new messages. */
const SCROLL_PIN_THRESHOLD_PX = 80;

export interface ModularOnboardingProps {
  onComplete: () => void;
}

export function ModularOnboarding({ onComplete }: ModularOnboardingProps) {
  const hook = useModularOnboarding();
  const scrollRef = useRef<HTMLDivElement>(null);
  const stickToBottomRef = useRef(true);

  useEffect(() => {
    if (hook.phase === 'complete') {
      onComplete();
    }
  }, [hook.phase, onComplete]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const updateStickToBottom = () => {
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
      stickToBottomRef.current = distanceFromBottom <= SCROLL_PIN_THRESHOLD_PX;
    };
    updateStickToBottom();
    el.addEventListener('scroll', updateStickToBottom, { passive: true });
    return () => el.removeEventListener('scroll', updateStickToBottom);
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || !stickToBottomRef.current) return;
    el.scrollTop = el.scrollHeight;
  }, [hook.messages.length, hook.isTyping]);

  return (
    <div className="grid min-h-0 grid-cols-1 lg:grid-cols-[45%_55%] h-dvh overflow-hidden">
      <div className="flex min-h-0 flex-col h-full border-r border-slate-200">
        {hook.error != null && (
          <div className="shrink-0 bg-red-50 border-b border-red-200 px-4 py-2 text-sm text-red-800">
            {hook.error}
          </div>
        )}
        <div
          ref={scrollRef}
          className="flex-1 min-h-0 overflow-y-auto px-4 py-6 space-y-3 [scrollbar-width:thin] [scrollbar-color:rgb(203_213_225)_transparent] [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-thumb]:rounded [&::-webkit-scrollbar-thumb]:bg-slate-300"
        >
          {hook.messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {hook.isTyping && <TypingIndicator />}
        </div>
        <div className="shrink-0 bg-white">
          <InputBar
            inputHint={hook.inputHint}
            onSend={hook.sendUserMessage}
            disabled={
              hook.phase === 'committing' ||
              hook.phase === 'hard_cap' ||
              hook.phase === 'complete'
            }
            phase={hook.phase}
          />
        </div>
      </div>
      <div className="min-h-0 overflow-y-auto">
        <OnboardingCanvas
          modules={hook.modules}
          currentModule={hook.currentModule}
          data={hook.data}
          phase={hook.phase}
          progressPct={hook.progressPct}
          completedCount={hook.completedCount}
          commitField={hook.commitField}
          revisitModule={hook.revisitModule}
          skipCurrentModule={hook.skipCurrentModule}
          commitCurrentModule={hook.commitCurrentModule}
          userTier={hook.userTier}
        />
      </div>
    </div>
  );
}
