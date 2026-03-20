import { useState } from "react";

type Priority = "critical" | "recommended" | "polish";
type Status = "open" | "in-progress" | "fixed";
type FilterKey = "all" | "critical" | "recommended" | "polish" | "fixed";

interface PreLaunchItem {
  id: string;
  priority: Priority;
  status: Status;
  suite: string;
  test: string;
  title: string;
  detail: string;
  file: string;
}

const INITIAL_ITEMS: PreLaunchItem[] = [
  // CRITICAL
  {
    id: "FIX-01", priority: "critical", status: "open",
    suite: "Auth", test: "AUTH-05",
    title: "Rate limiter not Redis-backed",
    detail: "In-memory rate limiter resets on restart and doesn't work across workers. Replace with Redis-backed flask-limiter using X-Real-IP header.",
    file: "backend/app.py"
  },
  {
    id: "FIX-02", priority: "critical", status: "open",
    suite: "Data", test: "DP-01",
    title: "Assessments stored in SQLite, not PostgreSQL",
    detail: "Write lock contention at 10+ concurrent users. SQLite path also breaks when CWD ≠ /var/www/mingus. Migrate to existing PostgreSQL instance.",
    file: "backend/assessments/"
  },
  {
    id: "FIX-03", priority: "critical", status: "open",
    suite: "Accessibility", test: "ACC-06",
    title: "Login page has no <h1>",
    detail: 'WCAG 2.1 failure. Login page only has <h2>"Sign in to your account". Screen readers expect a page-level heading. Change to <h1>.',
    file: "frontend/src/pages/Login.tsx"
  },
  {
    id: "FIX-04", priority: "critical", status: "open",
    suite: "Mobile", test: "MOB-05",
    title: 'Main "Get Started" CTA button only 32px tall',
    detail: "12px below Apple's 44px minimum touch target. Increase vertical padding in Tailwind (e.g. py-3 → py-4).",
    file: "frontend/src/components/LandingPage.tsx"
  },
  // RECOMMENDED
  {
    id: "FIX-05", priority: "recommended", status: "open",
    suite: "UX", test: "—",
    title: "No profile editing after onboarding",
    detail: "UserProfile.tsx is an onboarding wizard only. No edit flow exists post-setup. Users cannot update their info after completing onboarding.",
    file: "frontend/src/components/UserProfile.tsx"
  },
  {
    id: "FIX-06", priority: "recommended", status: "open",
    suite: "Accessibility", test: "ACC-06",
    title: "Two <h1> tags on landing page",
    detail: 'Landing has "Mingus" and "Financial Wellness Built For The Underdogs" both as H1. Demote second to H2.',
    file: "frontend/src/components/LandingPage.tsx"
  },
  {
    id: "FIX-07", priority: "recommended", status: "open",
    suite: "Accessibility", test: "ACC-11",
    title: 'Error message missing role="alert"',
    detail: '"Invalid email or password" is visible but has no role="alert" or aria-live. Screen readers will not announce it automatically.',
    file: "frontend/src/pages/Login.tsx"
  },
  {
    id: "FIX-08", priority: "recommended", status: "open",
    suite: "Mobile", test: "MOB-05",
    title: "Mobile menu hamburger button is 40px (needs 44px)",
    detail: "4px short of minimum touch target. Add min-h-[44px] min-w-[44px] in Tailwind.",
    file: "frontend/src/components/Navbar.tsx"
  },
  {
    id: "FIX-09", priority: "recommended", status: "open",
    suite: "Mobile", test: "MOB-05",
    title: '"Skip assessments" link is 20px tall',
    detail: "Secondary action but still tappable UI. Increase padding or convert to button to meet minimum touch target.",
    file: "frontend/src/components/LandingPage.tsx"
  },
  {
    id: "FIX-10", priority: "recommended", status: "open",
    suite: "Accessibility", test: "ACC-09",
    title: "6 text elements fail 4.5:1 contrast ratio",
    detail: 'Failing: "For The Underdogs" overlay, stat labels (Wellness Score, Cash Flow, Next Milestone), "+$2,340" value, "FREE" badge. Need darker text or adjusted backgrounds.',
    file: "frontend/src/components/LandingPage.tsx"
  },
  {
    id: "FIX-11", priority: "recommended", status: "open",
    suite: "Security", test: "—",
    title: "Rotate production secrets before launch",
    detail: "RESEND_API_KEY (live email key in systemd file), JWT_SECRET_KEY, and DATABASE_URL password must all be rotated before go-live.",
    file: "/etc/systemd/system/mingus-test.service"
  },
  // POLISH
  {
    id: "FIX-12", priority: "polish", status: "open",
    suite: "Accessibility", test: "ACC-14",
    title: "Login and landing share the same <title>",
    detail: 'Both pages show "Mingus - Personal Finance App". Login should be "Sign In — Mingus" for better screen reader and tab UX.',
    file: "frontend/src/pages/Login.tsx"
  },
  {
    id: "FIX-13", priority: "polish", status: "open",
    suite: "Performance", test: "PERF-03/04",
    title: "Lighthouse scores unknown",
    detail: "PERF-03/04 skip in headless mode. Run lighthouse https://test.mingusapp.com/ --view locally to get Core Web Vitals before launch.",
    file: "—"
  },
  {
    id: "FIX-14", priority: "polish", status: "open",
    suite: "Mobile", test: "MOB-05",
    title: "Skip-to-content links are 16px tall",
    detail: "Three skip links (main content, navigation, footer) are only 16px. Add padding for mobile usability.",
    file: "frontend/src/components/LandingPage.tsx"
  },
  {
    id: "FIX-15", priority: "polish", status: "open",
    suite: "UX", test: "—",
    title: "No breadcrumb navigation",
    detail: "Deferred by design but recommended for deep-linked pages before launch.",
    file: "—"
  },
];

const PRIORITY_CONFIG: Record<Priority, { label: string; color: string; bg: string; border: string; dot: string }> = {
  critical: { label: "Critical", color: "#FF4444", bg: "#FF444415", border: "#FF444440", dot: "🔴" },
  recommended: { label: "Recommended", color: "#F59E0B", bg: "#F59E0B15", border: "#F59E0B40", dot: "🟡" },
  polish: { label: "Polish", color: "#22C55E", bg: "#22C55E15", border: "#22C55E40", dot: "🟢" },
};

const STATUS_CONFIG: Record<Status, { label: string; color: string; bg: string }> = {
  open: { label: "Open", color: "#94A3B8", bg: "#1E293B" },
  "in-progress": { label: "In Progress", color: "#60A5FA", bg: "#1E3A5F" },
  fixed: { label: "Fixed", color: "#34D399", bg: "#064E3B" },
};

export default function PreLaunchTracker() {
  const [items, setItems] = useState<PreLaunchItem[]>(INITIAL_ITEMS);
  const [filter, setFilter] = useState<FilterKey>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleStatus = (id: string) => {
    setItems(prev => prev.map(item => {
      if (item.id !== id) return item;
      const cycle: Record<Status, Status> = { open: "in-progress", "in-progress": "fixed", fixed: "open" };
      return { ...item, status: cycle[item.status] };
    }));
  };

  const filtered = filter === "all" ? items : items.filter(i =>
    filter === "fixed" ? i.status === "fixed" : (i.priority === filter && i.status !== "fixed")
  );

  const counts = {
    total: items.length,
    fixed: items.filter(i => i.status === "fixed").length,
    critical: items.filter(i => i.priority === "critical" && i.status !== "fixed").length,
    recommended: items.filter(i => i.priority === "recommended" && i.status !== "fixed").length,
    polish: items.filter(i => i.priority === "polish" && i.status !== "fixed").length,
  };

  const pct = Math.round((counts.fixed / counts.total) * 100);

  return (
    <div style={{
      fontFamily: "'DM Mono', 'Courier New', monospace",
      background: "#0A0F1E",
      minHeight: "100vh",
      color: "#E2E8F0",
      padding: "24px 20px",
    }}>
      {/* Header */}
      <div style={{ maxWidth: 780, margin: "0 auto" }}>
        <div style={{ marginBottom: 28 }}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
            <div>
              <div style={{ fontSize: 10, letterSpacing: "0.2em", color: "#475569", textTransform: "uppercase", marginBottom: 6 }}>
                MINGUS · PRE-LAUNCH
              </div>
              <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: "#F1F5F9", letterSpacing: "-0.02em" }}>
                Fix Tracker
              </h1>
              <div style={{ fontSize: 12, color: "#64748B", marginTop: 4 }}>
                {counts.fixed}/{counts.total} resolved · Click any item to cycle status
              </div>
            </div>

            {/* Progress ring */}
            <div style={{ position: "relative", width: 64, height: 64, flexShrink: 0 }}>
              <svg width="64" height="64" style={{ transform: "rotate(-90deg)" }}>
                <circle cx="32" cy="32" r="26" fill="none" stroke="#1E293B" strokeWidth="5" />
                <circle cx="32" cy="32" r="26" fill="none"
                  stroke={pct === 100 ? "#34D399" : pct > 50 ? "#60A5FA" : "#F59E0B"}
                  strokeWidth="5"
                  strokeDasharray={`${2 * Math.PI * 26}`}
                  strokeDashoffset={`${2 * Math.PI * 26 * (1 - pct / 100)}`}
                  strokeLinecap="round"
                  style={{ transition: "stroke-dashoffset 0.5s ease" }}
                />
              </svg>
              <div style={{
                position: "absolute", inset: 0, display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center",
              }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: "#F1F5F9", lineHeight: 1 }}>{pct}%</span>
              </div>
            </div>
          </div>

          {/* Stat pills */}
          <div style={{ display: "flex", gap: 8, marginTop: 16, flexWrap: "wrap" }}>
            {[
              { key: "all" as const, label: `All  ${counts.total}`, color: "#94A3B8", activeBg: "#1E293B" },
              { key: "critical" as const, label: `🔴  ${counts.critical} Critical`, color: "#FF4444", activeBg: "#FF444420" },
              { key: "recommended" as const, label: `🟡  ${counts.recommended} Recommended`, color: "#F59E0B", activeBg: "#F59E0B20" },
              { key: "polish" as const, label: `🟢  ${counts.polish} Polish`, color: "#22C55E", activeBg: "#22C55E20" },
              { key: "fixed" as const, label: `✓  ${counts.fixed} Fixed`, color: "#34D399", activeBg: "#34D39920" },
            ].map(f => (
              <button key={f.key} onClick={() => setFilter(f.key)} style={{
                padding: "5px 12px", borderRadius: 6, border: `1px solid ${filter === f.key ? f.color : "#1E293B"}`,
                background: filter === f.key ? f.activeBg : "transparent",
                color: filter === f.key ? f.color : "#475569",
                fontSize: 11, fontFamily: "inherit", cursor: "pointer",
                transition: "all 0.15s", fontWeight: filter === f.key ? 700 : 400,
              }}>
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Items */}
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {filtered.length === 0 && (
            <div style={{ textAlign: "center", padding: "40px 0", color: "#334155", fontSize: 13 }}>
              {filter === "fixed" ? "Nothing fixed yet — keep going!" : "Nothing here."}
            </div>
          )}

          {filtered.map(item => {
            const p = PRIORITY_CONFIG[item.priority];
            const s = STATUS_CONFIG[item.status];
            const isExpanded = expandedId === item.id;
            const isFixed = item.status === "fixed";

            return (
              <div key={item.id}
                style={{
                  border: `1px solid ${isFixed ? "#064E3B" : p.border}`,
                  borderRadius: 8,
                  background: isFixed ? "#0A1F1A" : "#0D1626",
                  overflow: "hidden",
                  transition: "all 0.2s",
                  opacity: isFixed ? 0.6 : 1,
                }}
              >
                {/* Row */}
                <div
                  style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", cursor: "pointer" }}
                  onClick={() => setExpandedId(isExpanded ? null : item.id)}
                >
                  {/* Status toggle */}
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleStatus(item.id); }}
                    title="Click to cycle status"
                    style={{
                      width: 22, height: 22, borderRadius: 4, border: `1.5px solid ${s.color}`,
                      background: s.bg, color: s.color, fontSize: 10, fontFamily: "inherit",
                      cursor: "pointer", flexShrink: 0, display: "flex", alignItems: "center",
                      justifyContent: "center", padding: 0, transition: "all 0.15s",
                    }}
                  >
                    {isFixed ? "✓" : item.status === "in-progress" ? "▸" : "○"}
                  </button>

                  {/* ID */}
                  <span style={{ fontSize: 10, color: "#334155", fontWeight: 700, flexShrink: 0, width: 46 }}>
                    {item.id}
                  </span>

                  {/* Priority dot */}
                  <span style={{ fontSize: 9, flexShrink: 0 }}>{p.dot}</span>

                  {/* Title */}
                  <span style={{
                    fontSize: 12, color: isFixed ? "#4B6A5E" : "#CBD5E1",
                    flex: 1, fontWeight: 500,
                    textDecoration: isFixed ? "line-through" : "none",
                  }}>
                    {item.title}
                  </span>

                  {/* Suite tag */}
                  <span style={{
                    fontSize: 10, padding: "2px 7px", borderRadius: 4,
                    background: "#1E293B", color: "#475569", flexShrink: 0,
                  }}>
                    {item.suite}
                  </span>

                  {/* Test tag */}
                  <span style={{ fontSize: 10, color: "#334155", flexShrink: 0, width: 58, textAlign: "right" }}>
                    {item.test}
                  </span>

                  {/* Expand arrow */}
                  <span style={{ fontSize: 10, color: "#334155", transition: "transform 0.2s", transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)", flexShrink: 0 }}>▼</span>
                </div>

                {/* Expanded detail */}
                {isExpanded && (
                  <div style={{
                    borderTop: `1px solid #1E293B`,
                    padding: "12px 14px",
                    background: "#0A0F1E",
                  }}>
                    <p style={{ margin: "0 0 10px", fontSize: 12, color: "#94A3B8", lineHeight: 1.6 }}>
                      {item.detail}
                    </p>
                    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                      <div style={{ fontSize: 11, color: "#334155" }}>
                        <span style={{ color: "#475569" }}>file: </span>
                        <span style={{ color: "#60A5FA" }}>{item.file}</span>
                      </div>
                      <div style={{ fontSize: 11, color: "#334155" }}>
                        <span style={{ color: "#475569" }}>status: </span>
                        <span style={{ color: s.color }}>{s.label}</span>
                      </div>
                      {/* Cycle status button */}
                      <button onClick={() => toggleStatus(item.id)} style={{
                        marginLeft: "auto", fontSize: 11, padding: "4px 10px", borderRadius: 5,
                        border: `1px solid ${s.color}40`, background: s.bg,
                        color: s.color, fontFamily: "inherit", cursor: "pointer",
                      }}>
                        Mark as {item.status === "open" ? "In Progress" : item.status === "in-progress" ? "Fixed" : "Open"} →
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div style={{ marginTop: 20, fontSize: 10, color: "#1E293B", textAlign: "center" }}>
          Last updated: March 2026 · Mingus Test Suite v1.0 · 119 tests across 11 suites
        </div>
      </div>
    </div>
  );
}
