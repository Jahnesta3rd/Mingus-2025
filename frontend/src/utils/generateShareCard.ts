/** Instagram Story dimensions (9:16) */
export const SHARE_CARD_WIDTH = 1080;
export const SHARE_CARD_HEIGHT = 1920;

const BG_TOP = "#0d0a08";
const BG_BOTTOM = "#1a1520";
const GOLD = "#C4A064";
const CREAM = "#f0e8d8";
const WHITE = "#ffffff";

const FONT_DISPLAY = '"Playfair Display", Georgia, "Times New Roman", serif';
const FONT_SANS = '"Inter", system-ui, -apple-system, sans-serif';
const FONT_EMOJI =
  '200px "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", "EmojiOne Color", sans-serif';

let fontsPromise: Promise<void> | null = null;

async function loadFontsFromGoogleCss(cssUrl: string): Promise<void> {
  const css = await fetch(cssUrl).then((r) => {
    if (!r.ok) throw new Error(`Font CSS failed: ${r.status}`);
    return r.text();
  });
  const blocks = css.split("@font-face").slice(1);
  const loads: Promise<FontFace>[] = [];
  for (const block of blocks) {
    if (!block.includes("woff2")) continue;
    const familyMatch = block.match(/font-family:\s*['"]?([^;'"]+)['"]?/);
    const weightMatch = block.match(/font-weight:\s*(\d+)/);
    const urlMatch = block.match(/url\(([^)]+)\)\s*format\(['"]woff2['"]\)/);
    if (!familyMatch || !urlMatch) continue;
    const rawFamily = familyMatch[1].replace(/\+/g, " ").trim();
    const weight = weightMatch?.[1] ?? "400";
    const ff = new FontFace(rawFamily, `url(${urlMatch[1].trim()})`, {
      weight,
      style: "normal",
    });
    loads.push(ff.load().then((loaded) => loaded));
  }
  const faces = await Promise.all(loads);
  for (const f of faces) {
    document.fonts.add(f);
  }
}

/**
 * Load Playfair Display + Inter via FontFace API (woff2 from Google Fonts CSS).
 */
export function ensureShareCardFontsLoaded(): Promise<void> {
  if (!fontsPromise) {
    const css =
      "https://fonts.googleapis.com/css2?" +
      "family=Playfair+Display:wght@400;600;700&family=Inter:wght@400;600;700&display=swap";
    fontsPromise = loadFontsFromGoogleCss(css).catch(() => {
      fontsPromise = null;
    });
  }
  return fontsPromise ?? Promise.resolve();
}

/**
 * Hostname shown on the card (e.g. vibecheckups.com). Falls back to current origin.
 */
export function getShareCardFooterLabel(): string {
  try {
    const raw = import.meta.env.VITE_PUBLIC_SITE_URL as string | undefined;
    if (raw?.trim()) {
      const href = raw.startsWith("http") ? raw : `https://${raw}`;
      return new URL(href).hostname.replace(/^www\./i, "");
    }
  } catch {
    /* ignore */
  }
  if (typeof window !== "undefined") {
    return window.location.hostname.replace(/^www\./i, "");
  }
  return "vibecheckups.com";
}

function drawGradientBackground(ctx: CanvasRenderingContext2D): void {
  const g = ctx.createLinearGradient(0, 0, 0, SHARE_CARD_HEIGHT);
  g.addColorStop(0, BG_TOP);
  g.addColorStop(1, BG_BOTTOM);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, SHARE_CARD_WIDTH, SHARE_CARD_HEIGHT);
}

function truncateLine(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string {
  if (ctx.measureText(text).width <= maxWidth) return text;
  const ell = "…";
  let low = 0;
  let high = text.length;
  while (low < high) {
    const mid = Math.ceil((low + high) / 2);
    const slice = text.slice(0, mid) + ell;
    if (ctx.measureText(slice).width <= maxWidth) low = mid;
    else high = mid - 1;
  }
  return text.slice(0, low) + ell;
}

function drawShareCardContents(
  ctx: CanvasRenderingContext2D,
  verdict_label: string,
  verdict_emoji: string,
  verdict_description: string
): void {
  drawGradientBackground(ctx);

  const padX = 72;
  const maxTextW = SHARE_CARD_WIDTH - padX * 2;
  const titleY = 110;

  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillStyle = GOLD;
  ctx.font = `600 26px ${FONT_DISPLAY}`;
  ctx.fillText("VIBE CHECKUPS™", SHARE_CARD_WIDTH / 2, titleY);

  const footerLabel = getShareCardFooterLabel();
  const footerY = SHARE_CARD_HEIGHT - 72;
  ctx.font = `600 22px ${FONT_DISPLAY}`;
  ctx.fillStyle = GOLD;
  ctx.fillText(footerLabel, SHARE_CARD_WIDTH / 2, footerY);

  const labelFont = `700 52px ${FONT_SANS}`;
  const descFont = `400 28px ${FONT_SANS}`;
  const ruleW = Math.min(420, maxTextW * 0.55);
  const gapEmojiLabel = 36;
  const gapLabelRule = 40;
  const gapRuleDesc = 32;
  const labelH = 52;
  const emojiH = 200;
  const descH = 34;

  ctx.font = descFont;
  const descOneLine = truncateLine(ctx, verdict_description.trim(), maxTextW);

  const blockH = emojiH + gapEmojiLabel + labelH + gapLabelRule + 2 + gapRuleDesc + descH;
  const topContent = titleY + 100;
  const bottomContent = footerY - 90;
  const midY = topContent + (bottomContent - topContent) / 2;
  let y = midY - blockH / 2;

  ctx.font = FONT_EMOJI;
  ctx.textBaseline = "middle";
  ctx.fillStyle = WHITE;
  ctx.fillText(verdict_emoji || "✨", SHARE_CARD_WIDTH / 2, y + emojiH / 2);

  y += emojiH + gapEmojiLabel;

  ctx.font = labelFont;
  ctx.fillStyle = WHITE;
  const labelText = truncateLine(ctx, verdict_label.trim().replace(/\s+/g, " "), maxTextW);
  ctx.fillText(labelText, SHARE_CARD_WIDTH / 2, y + labelH / 2);

  y += labelH + gapLabelRule;

  ctx.strokeStyle = GOLD;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(SHARE_CARD_WIDTH / 2 - ruleW / 2, y + 1);
  ctx.lineTo(SHARE_CARD_WIDTH / 2 + ruleW / 2, y + 1);
  ctx.stroke();

  y += 2 + gapRuleDesc;

  ctx.font = descFont;
  ctx.fillStyle = CREAM;
  ctx.fillText(descOneLine, SHARE_CARD_WIDTH / 2, y + descH / 2);
}

/**
 * Draw the share card onto a canvas (mutates width/height to full resolution).
 */
export async function renderShareCard(
  canvas: HTMLCanvasElement,
  verdict_label: string,
  verdict_emoji: string,
  verdict_description: string
): Promise<void> {
  await ensureShareCardFontsLoaded();
  canvas.width = SHARE_CARD_WIDTH;
  canvas.height = SHARE_CARD_HEIGHT;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Could not get 2D context");
  drawShareCardContents(ctx, verdict_label, verdict_emoji, verdict_description);
}

/**
 * Renders an Instagram Story PNG (1080×1920) for the given verdict.
 */
export function generateShareCard(
  verdict_label: string,
  verdict_emoji: string,
  verdict_description: string
): Promise<Blob> {
  const canvas = document.createElement("canvas");
  return renderShareCard(canvas, verdict_label, verdict_emoji, verdict_description).then(
    () =>
      new Promise<Blob>((resolve, reject) => {
        canvas.toBlob((blob) => {
          if (blob) resolve(blob);
          else reject(new Error("canvas.toBlob returned null"));
        }, "image/png");
      })
  );
}
