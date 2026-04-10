import { useCallback, useState } from "react";
import { VEHICLE_CHECK_QUESTIONS } from "./vehicleCheckQuestions";

type VehicleCheckQuizPanelProps = {
  onComplete: (answers: Record<string, number>) => void;
  onError: (msg: string | null) => void;
  busy?: boolean;
};

export function VehicleCheckQuizPanel({ onComplete, onError, busy = false }: VehicleCheckQuizPanelProps) {
  const [started, setStarted] = useState(false);
  const [qIndex, setQIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});

  const totalQs = VEHICLE_CHECK_QUESTIONS.length;
  const currentQ = VEHICLE_CHECK_QUESTIONS[qIndex];
  const progressPct = Math.round(((qIndex + 1) / totalQs) * 100);

  const pickOption = useCallback(
    (value: number) => {
      if (!currentQ || busy) return;
      onError(null);
      const key = String(currentQ.id);
      const next = { ...answers, [key]: value };
      setAnswers(next);
      if (qIndex + 1 >= totalQs) {
        onComplete(next);
      } else {
        setQIndex((i) => i + 1);
      }
    },
    [answers, busy, currentQ, onComplete, onError, qIndex, totalQs]
  );

  if (!started) {
    return (
      <div className="space-y-6 text-center">
        <p className="text-sm leading-relaxed text-[#9a8f7e]">
          10 questions. Your answers estimate maintenance risk and annual upkeep — for planning, not a mechanical
          diagnosis.
        </p>
        <button
          type="button"
          onClick={() => setStarted(true)}
          disabled={busy}
          className="w-full rounded-xl bg-[#C4A064] py-3.5 text-sm font-semibold text-[#0d0a08] shadow-landing-card transition hover:bg-[#d4b074] disabled:opacity-45"
        >
          Begin Vehicle Health
        </button>
      </div>
    );
  }

  if (!currentQ) return null;

  return (
    <div className="space-y-6">
      <div className="flex justify-between text-xs uppercase tracking-wider text-[#9a8f7e]">
        <span>Vehicle &amp; cost risk</span>
        <span>
          {qIndex + 1} / {totalQs}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-[#2a2030]">
        <div
          className="h-full rounded-full bg-[#C4A064] transition-all duration-300"
          style={{ width: `${Math.min(100, progressPct)}%` }}
        />
      </div>
      <h3 className="font-display text-xl font-semibold text-[#f0e8d8] sm:text-2xl">{currentQ.prompt}</h3>
      <div className="grid gap-3">
        {currentQ.options.map((opt, idx) => (
          <button
            key={opt.label}
            type="button"
            disabled={busy}
            onClick={() => pickOption(opt.value)}
            className="rounded-xl border border-[#2a2030] bg-[#1a1520] px-4 py-3.5 text-left text-sm text-[#f0e8d8] transition hover:border-[#C4A064]/50 disabled:opacity-45"
          >
            <span className="mr-2 font-mono text-xs text-[#C4A064]">{idx}</span>
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
