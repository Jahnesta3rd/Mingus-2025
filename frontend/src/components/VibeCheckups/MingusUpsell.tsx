import { useCallback, useState } from "react";

type VcPost = <T,>(path: string, body?: Record<string, unknown>) => Promise<T>;

export type MingusUpsellProps = {
  leadId: string;
  vcPost: VcPost;
};

/** Maps to POST /lead/{id}/track-event (Vibe Checkups funnel analytics). */
async function trackLeadFunnelEvent(leadId: string, eventType: string, vcPost: VcPost): Promise<void> {
  await vcPost(`/lead/${encodeURIComponent(leadId)}/track-event`, {
    event_type: eventType,
    event_data: {},
  });
}

export function MingusUpsell({ leadId, vcPost }: MingusUpsellProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCta = useCallback(async () => {
    setError(null);
    setBusy(true);
    try {
      await trackLeadFunnelEvent(leadId, "mingus_cta_clicked", vcPost);
      const data = await vcPost<{ redirect_url: string }>(
        `/lead/${encodeURIComponent(leadId)}/convert-to-mingus`,
        {}
      );
      window.location.assign(data.redirect_url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
      setBusy(false);
    }
  }, [leadId, vcPost]);

  const bullets = [
    { icon: "💰", text: "Track your real income vs. your financial goals" },
    { icon: "📊", text: "See your wealth trajectory — not just your budget" },
    { icon: "🧠", text: "Built specifically for Black professionals building generational wealth" },
  ];

  return (
    <div className="rounded-2xl border border-[#C4A064]/40 bg-gradient-to-br from-[#C4A064]/14 via-[#1a1520]/80 to-[#0d0a08] p-6 sm:p-8 shadow-landing-card">
      <h3 className="font-display text-xl font-semibold text-[#f0e8d8] sm:text-2xl">
        Now let&apos;s talk about your money.
      </h3>
      <p className="mt-3 text-sm leading-relaxed text-[#9a8f7e] sm:text-base">
        You just saw what this relationship could cost you. Mingus helps you build what you&apos;re actually worth.
      </p>
      <ul className="mt-6 space-y-4 text-left text-sm text-[#f0e8d8]/95 sm:text-base">
        {bullets.map((b) => (
          <li key={b.text} className="flex gap-3">
            <span className="shrink-0 text-lg leading-6" aria-hidden>
              {b.icon}
            </span>
            <span className="leading-snug">{b.text}</span>
          </li>
        ))}
      </ul>
      <button
        type="button"
        disabled={busy}
        onClick={() => void handleCta()}
        className="mt-8 flex w-full items-center justify-center rounded-xl bg-[#C4A064] py-3.5 text-center text-sm font-semibold text-[#0d0a08] transition hover:bg-[#d4b074] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {busy ? "Taking you there…" : "Start My Free Mingus Trial"}
      </button>
      <p className="mt-3 text-center text-xs text-[#9a8f7e] sm:text-sm">
        No credit card required · Cancel anytime · Takes 2 minutes
      </p>
      {error && (
        <p className="mt-3 text-center text-sm text-rose-400" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
