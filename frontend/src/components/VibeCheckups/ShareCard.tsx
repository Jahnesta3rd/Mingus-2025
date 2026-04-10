import { useCallback, useEffect, useRef, useState } from "react";
import { trackEvent } from "../../utils/trackEvent";
import {
  generateShareCard,
  renderShareCard,
  SHARE_CARD_HEIGHT,
  SHARE_CARD_WIDTH,
} from "../../utils/generateShareCard";

export type ShareCardProps = {
  verdict_label: string;
  verdict_emoji: string;
  verdict_description: string;
};

function vibeCheckupsShareUrl(): string {
  if (typeof window === "undefined") return "/vibe-checkups";
  return `${window.location.origin}/vibe-checkups`;
}

export function ShareCard({
  verdict_label,
  verdict_emoji,
  verdict_description,
}: ShareCardProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [copied, setCopied] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const el = canvasRef.current;
    if (!el) return;
    let cancelled = false;
    void (async () => {
      try {
        await renderShareCard(el, verdict_label, verdict_emoji, verdict_description);
      } catch {
        if (!cancelled && el.getContext("2d")) {
          /* preview may fail; download path still attempts render */
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [verdict_label, verdict_emoji, verdict_description]);

  const onDownload = useCallback(async () => {
    setDownloading(true);
    try {
      void trackEvent("share_card_generated", "export");
      const blob = await generateShareCard(verdict_label, verdict_emoji, verdict_description);
      const url = URL.createObjectURL(blob);
      const safeLabel = verdict_label.replace(/[^\w\d-]+/gi, "_").slice(0, 48) || "vibe-checkup";
      const a = document.createElement("a");
      a.href = url;
      a.download = `vibe-checkup-${safeLabel}.png`;
      a.rel = "noopener";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  }, [verdict_description, verdict_emoji, verdict_label]);

  const onCopyLink = useCallback(async () => {
    const url = vibeCheckupsShareUrl();
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      return;
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }, []);

  return (
    <div className="flex flex-col items-center gap-4">
      <div
        className="overflow-hidden rounded-xl border border-[#2a2030] shadow-landing-card"
        style={{ width: 270, height: 480 }}
      >
        <canvas
          ref={canvasRef}
          width={SHARE_CARD_WIDTH}
          height={SHARE_CARD_HEIGHT}
          className="block h-full w-full"
          aria-label="Preview of your Vibe Checkups share card"
        />
      </div>

      <div className="flex w-full max-w-sm flex-col gap-3">
        <button
          type="button"
          onClick={() => void onDownload()}
          disabled={downloading}
          className="w-full rounded-xl bg-[#C4A064] py-3.5 text-sm font-semibold text-[#0d0a08] transition hover:bg-[#d4b074] disabled:opacity-60"
        >
          {downloading ? "Preparing…" : "Download Card"}
        </button>
        <button
          type="button"
          onClick={() => void onCopyLink()}
          className="w-full rounded-xl border border-[#2a2030] py-3.5 text-sm font-medium text-[#f0e8d8] transition hover:border-[#C4A064]/40"
        >
          Copy Link
        </button>
      </div>

      <div className="flex min-h-[1.375rem] items-center justify-center" aria-live="polite">
        {copied ? (
          <p className="text-sm font-medium text-[#C4A064]" role="status">
            Copied!
          </p>
        ) : null}
      </div>

      <p className="text-center text-xs text-[#9a8f7e]">Tag us @mingusapp when you post 🙌</p>
    </div>
  );
}
