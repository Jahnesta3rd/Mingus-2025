import { useEffect, useRef } from 'react';
import { useModularOnboarding } from '../hooks/useModularOnboarding';
import { OnboardingCanvas } from './OnboardingCanvas';
import { InputBar } from './chat/InputBar';
import { MessageBubble } from './chat/MessageBubble';
import { TypingIndicator } from './chat/TypingIndicator';

export interface ModularOnboardingProps {
  onComplete: () => void;
}

export function ModularOnboarding({ onComplete }: ModularOnboardingProps) {
  const hook = useModularOnboarding();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (hook.phase === 'complete') {
      onComplete();
    }
  }, [hook.phase, onComplete]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [hook.messages.length, hook.isTyping]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[45%_55%] h-screen overflow-hidden">
      <div className="flex flex-col h-full border-r border-slate-200">
        {hook.error != null && (
          <div className="bg-red-50 border-b border-red-200 px-4 py-2 text-sm text-red-800">
            {hook.error}
          </div>
        )}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-4 py-6 space-y-3"
        >
          {hook.messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {hook.isTyping && <TypingIndicator />}
        </div>
        <div className="shrink-0 max-h-[40vh] overflow-y-auto bg-white">
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
      <div className="overflow-y-auto">
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
