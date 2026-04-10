import { MingusUpsell } from "../VibeCheckups/MingusUpsell";
import { ShareCard } from "../VibeCheckups/ShareCard";
import type { ProjectionRow, Verdict } from "./vibeCheckupsTypes";

type VcPost = <T,>(path: string, body?: Record<string, unknown>) => Promise<T>;

function yearTotalColor(total: number): string {
  if (total > 6000) return "text-rose-400";
  if (total > 3000) return "text-amber-400";
  return "text-emerald-400";
}

type ProjectionUnlockProps = {
  projection: ProjectionRow[];
  verdict: Verdict | null;
  onRestart: () => void;
  leadId: string;
  vcPost: VcPost;
};

export function ProjectionUnlock({
  projection,
  verdict,
  onRestart,
  leadId,
  vcPost,
}: ProjectionUnlockProps) {
  const yearTotal =
    projection.length > 0 ? projection[projection.length - 1].cumulative_cost : 0;
  const totalCls = yearTotalColor(yearTotal);

  return (
    <div className="mx-auto max-w-lg space-y-8">
      <div className="space-y-2 text-center">
        <h2 className="font-display text-2xl font-semibold text-[#f0e8d8]">Your 12-month snapshot</h2>
        <p className="text-sm text-[#9a8f7e]">
          Month-by-month estimate — dining, gifts, travel, and the small stuff that adds up.
        </p>
      </div>

      <div className="overflow-hidden rounded-2xl border border-[#2a2030] bg-[#1a1520]/60 shadow-landing-card">
        <div className="max-h-80 overflow-y-auto">
          <table className="w-full text-left text-sm text-[#f0e8d8]">
            <thead className="sticky top-0 z-[1] bg-[#1a1520] text-xs uppercase tracking-wider text-[#9a8f7e]">
              <tr>
                <th className="px-4 py-3 font-medium">#</th>
                <th className="px-4 py-3 font-medium">Milestone</th>
                <th className="px-4 py-3 text-right font-medium">This month</th>
                <th className="px-4 py-3 text-right font-medium">Running total</th>
              </tr>
            </thead>
            <tbody>
              {projection.map((row) => (
                <tr key={row.month} className="border-t border-[#2a2030]/80">
                  <td className="px-4 py-2.5 tabular-nums text-[#C4A064]">{row.month}</td>
                  <td className="px-4 py-2.5 text-[#f0e8d8]/90">{row.event}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">${row.monthly_cost.toLocaleString()}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums font-medium text-[#f0e8d8]">
                    ${row.cumulative_cost.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div
        className={`rounded-2xl border border-[#2a2030] bg-[#1a1520] px-6 py-6 text-center ${totalCls}`}
      >
        <p className="text-xs font-medium uppercase tracking-wider text-[#9a8f7e]">Year-one total</p>
        <p className={`mt-1 font-display text-3xl font-bold tabular-nums ${totalCls}`}>
          ${yearTotal.toLocaleString()}
        </p>
      </div>

      <div
        className="h-px w-full bg-gradient-to-r from-transparent via-[#C4A064] to-transparent opacity-90"
        role="separator"
        aria-hidden
      />

      <MingusUpsell leadId={leadId} vcPost={vcPost} />

      <div className="flex flex-col gap-3">
        {verdict && (
          <ShareCard
            verdict_label={verdict.verdict_label}
            verdict_emoji={verdict.verdict_emoji}
            verdict_description={verdict.verdict_description}
          />
        )}
        <button type="button" onClick={onRestart} className="text-sm text-[#9a8f7e] underline-offset-4 hover:underline">
          Start a new checkup
        </button>
      </div>
    </div>
  );
}
