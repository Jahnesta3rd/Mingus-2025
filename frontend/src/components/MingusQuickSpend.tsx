import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Check, Plus, X } from "lucide-react";
import {
  useQuickSpend,
  type QuickSpendPayload,
} from "../hooks/useQuickSpend";

interface SpendVibeOption {
  id: string;
  label: string;
  emoji: string;
  signal: string;
  merchantPriority: string[];
}

interface MerchantOption {
  id: string;
  name: string;
}

interface MerchantGroup {
  id: string;
  label: string;
  merchants: MerchantOption[];
}

const MERCHANT_GROUPS: MerchantGroup[] = [
  {
    id: "coffee_quick_bites",
    label: "Coffee & Quick Bites",
    merchants: [
      { id: "starbucks", name: "Starbucks" },
      { id: "dunkin", name: "Dunkin" },
      { id: "local_cafe", name: "Local café" },
    ],
  },
  {
    id: "fast_food",
    label: "Fast Food & Takeout",
    merchants: [
      { id: "mcdonalds", name: "McDonald's" },
      { id: "chipotle", name: "Chipotle" },
      { id: "doordash", name: "DoorDash order" },
    ],
  },
  {
    id: "groceries_convenience",
    label: "Groceries & Convenience",
    merchants: [
      { id: "7eleven", name: "7-Eleven" },
      { id: "walmart", name: "Walmart" },
      { id: "target", name: "Target run" },
    ],
  },
  {
    id: "rides_transit",
    label: "Rides & Transit",
    merchants: [
      { id: "uber", name: "Uber" },
      { id: "lyft", name: "Lyft" },
      { id: "transit", name: "Transit / parking" },
    ],
  },
  {
    id: "entertainment",
    label: "Entertainment",
    merchants: [
      { id: "streaming", name: "Streaming" },
      { id: "movies", name: "Movies / events" },
      { id: "games", name: "Games & apps" },
    ],
  },
  {
    id: "shopping_retail",
    label: "Shopping & Retail",
    merchants: [
      { id: "amazon", name: "Amazon" },
      { id: "clothing", name: "Clothing" },
      { id: "home_goods", name: "Home goods" },
    ],
  },
  {
    id: "bars_social",
    label: "Bars & Social",
    merchants: [
      { id: "bar_tab", name: "Bar tab" },
      { id: "restaurant", name: "Restaurant" },
      { id: "nightlife", name: "Nightlife" },
    ],
  },
  {
    id: "other",
    label: "Other",
    merchants: [{ id: "other", name: "Other merchant" }],
  },
];

const SPEND_VIBES: SpendVibeOption[] = [
  {
    id: "on_the_go_eats",
    label: "On-the-go eats",
    emoji: "🥡",
    signal: "convenience_food",
    merchantPriority: ["coffee_quick_bites", "fast_food", "groceries_convenience"],
  },
  {
    id: "stress_buy",
    label: "Stress buy",
    emoji: "😰",
    signal: "stress_spending",
    merchantPriority: ["shopping_retail", "fast_food", "entertainment"],
  },
  {
    id: "social_treat",
    label: "Social treat",
    emoji: "🎁",
    signal: "social_generosity",
    merchantPriority: ["bars_social", "fast_food", "coffee_quick_bites"],
  },
  {
    id: "impulse_grab",
    label: "Impulse grab",
    emoji: "⚡",
    signal: "impulse_spending",
    merchantPriority: ["groceries_convenience", "shopping_retail", "other"],
  },
  {
    id: "comfort_food",
    label: "Comfort food",
    emoji: "🍕",
    signal: "comfort_food",
    merchantPriority: ["fast_food", "coffee_quick_bites", "groceries_convenience"],
  },
  {
    id: "retail_therapy",
    label: "Retail therapy",
    emoji: "🛍️",
    signal: "retail_therapy",
    merchantPriority: ["shopping_retail", "entertainment", "other"],
  },
  {
    id: "night_out",
    label: "Night out",
    emoji: "🍸",
    signal: "social_spending",
    merchantPriority: ["bars_social", "rides_transit", "entertainment"],
  },
  {
    id: "boredom_buy",
    label: "Boredom buy",
    emoji: "📱",
    signal: "boredom_spending",
    merchantPriority: ["entertainment", "shopping_retail", "other"],
  },
  {
    id: "celebration",
    label: "Celebration",
    emoji: "🎉",
    signal: "celebration_spending",
    merchantPriority: ["bars_social", "fast_food", "shopping_retail"],
  },
  {
    id: "commute_snack",
    label: "Commute snack",
    emoji: "☕",
    signal: "convenience_food",
    merchantPriority: ["coffee_quick_bites", "groceries_convenience", "rides_transit"],
  },
  {
    id: "gift_giving",
    label: "Gift giving",
    emoji: "💐",
    signal: "social_generosity",
    merchantPriority: ["shopping_retail", "bars_social", "other"],
  },
  {
    id: "subscription_splurge",
    label: "Subscription splurge",
    emoji: "📺",
    signal: "subscription_spending",
    merchantPriority: ["entertainment", "other", "shopping_retail"],
  },
];

function formatMoney(n: number): string {
  return `$${n.toFixed(2)}`;
}

function vibeLabel(id: string): string {
  return SPEND_VIBES.find((v) => v.id === id)?.label ?? id.replace(/_/g, " ");
}

const MingusQuickSpend: React.FC = () => {
  const {
    logSpend,
    fetchToday,
    saving,
    saveError,
    todayLog,
    loadingToday,
  } = useQuickSpend();

  const [sheetOpen, setSheetOpen] = useState(false);
  const [amount, setAmount] = useState("");
  const [selectedVibe, setSelectedVibe] = useState<SpendVibeOption | null>(null);
  const [selectedGroup, setSelectedGroup] = useState<MerchantGroup | null>(null);
  const [selectedMerchant, setSelectedMerchant] = useState<MerchantOption | null>(null);
  const [success, setSuccess] = useState(false);
  const amountRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchToday();
  }, [fetchToday]);

  useEffect(() => {
    if (sheetOpen && amountRef.current) {
      amountRef.current.focus();
    }
  }, [sheetOpen]);

  const parsedAmount = useMemo(() => {
    const n = parseFloat(amount.replace(/[^0-9.]/g, ""));
    return Number.isFinite(n) ? n : 0;
  }, [amount]);

  const sortedGroups = useMemo(() => {
    if (!selectedVibe) return MERCHANT_GROUPS;
    const order = selectedVibe.merchantPriority;
    return [...MERCHANT_GROUPS].sort((a, b) => {
      const ai = order.indexOf(a.id);
      const bi = order.indexOf(b.id);
      const ar = ai === -1 ? 999 : ai;
      const br = bi === -1 ? 999 : bi;
      return ar - br;
    });
  }, [selectedVibe]);

  const canSave = parsedAmount > 0 && selectedVibe !== null && !saving;

  const resetSheet = useCallback(() => {
    setAmount("");
    setSelectedVibe(null);
    setSelectedGroup(null);
    setSelectedMerchant(null);
    setSuccess(false);
  }, []);

  const closeSheet = useCallback(() => {
    setSheetOpen(false);
    resetSheet();
  }, [resetSheet]);

  const handleSave = async () => {
    if (!selectedVibe || parsedAmount <= 0) return;
    const payload: QuickSpendPayload = {
      amount: parsedAmount,
      spend_vibe: selectedVibe.id,
      vibe_signal: selectedVibe.signal,
    };
    if (selectedMerchant) {
      payload.merchant_id = selectedMerchant.id;
      payload.merchant_name = selectedMerchant.name;
    }
    if (selectedGroup) {
      payload.merchant_group = selectedGroup.label;
    }
    try {
      await logSpend(payload);
      setSuccess(true);
      setTimeout(() => {
        closeSheet();
        fetchToday();
      }, 1300);
    } catch {
      /* saveError surfaced in sheet */
    }
  };

  return (
    <>
      <section
        aria-label="Today's quick spend log"
        style={{ padding: "16px 16px 96px", marginTop: 8 }}
      >
        <h2
          style={{
            fontSize: 14,
            fontWeight: 700,
            color: "#582C8E",
            margin: "0 0 8px",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
          }}
        >
          Quick spend today
        </h2>
        {loadingToday && !todayLog ? (
          <p style={{ color: "#6B7280", fontSize: 14, margin: 0 }}>Loading…</p>
        ) : todayLog && todayLog.count > 0 ? (
          <>
            <p style={{ margin: "0 0 12px", fontSize: 14, color: "#374151" }}>
              {todayLog.count} {todayLog.count === 1 ? "entry" : "entries"} ·{" "}
              <strong>{formatMoney(todayLog.total)}</strong>
            </p>
            <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {todayLog.entries.map((entry) => (
                <li
                  key={entry.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "10px 12px",
                    marginBottom: 8,
                    borderRadius: 12,
                    background: "rgba(88,44,142,0.08)",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14, color: "#1A1815" }}>
                      {entry.merchant_name ?? vibeLabel(entry.spend_vibe)}
                    </div>
                    <div style={{ fontSize: 12, color: "#6B7280" }}>
                      {vibeLabel(entry.spend_vibe)}
                    </div>
                  </div>
                  <div style={{ fontWeight: 700, color: "#582C8E" }}>
                    {formatMoney(entry.amount)}
                  </div>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p style={{ color: "#6B7280", fontSize: 14, margin: 0 }}>
            Tap + to log discretionary spend in seconds.
          </p>
        )}
      </section>

      <button
        type="button"
        aria-label="Log a purchase"
        onClick={() => setSheetOpen(true)}
        style={{
          position: "fixed",
          right: 20,
          bottom: 88,
          zIndex: 45,
          width: 56,
          height: 56,
          borderRadius: "50%",
          border: "none",
          background: "linear-gradient(135deg, #582C8E 0%, #7C3AED 100%)",
          color: "#fff",
          boxShadow: "0 8px 24px rgba(88,44,142,0.45)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
        }}
      >
        <Plus size={28} strokeWidth={2.5} aria-hidden />
      </button>

      {sheetOpen && (
        <div
          role="presentation"
          data-testid="quick-spend-backdrop"
          onClick={closeSheet}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.45)",
            zIndex: 50,
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Quick spend logger"
            onClick={(e) => e.stopPropagation()}
            style={{
              position: "fixed",
              left: 0,
              right: 0,
              bottom: 0,
              maxHeight: "92vh",
              overflowY: "auto",
              background: "#fff",
              borderTopLeftRadius: 20,
              borderTopRightRadius: 20,
              padding: "12px 16px 32px",
              zIndex: 51,
            }}
          >
            <div
              style={{
                width: 40,
                height: 4,
                borderRadius: 2,
                background: "#D1D5DB",
                margin: "0 auto 16px",
              }}
              aria-hidden
            />

            {success ? (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  padding: "48px 16px",
                  gap: 12,
                }}
              >
                <div
                  style={{
                    width: 64,
                    height: 64,
                    borderRadius: "50%",
                    background: "#582C8E",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Check color="#fff" size={32} aria-hidden />
                </div>
                <p style={{ fontSize: 18, fontWeight: 700, margin: 0, color: "#1A1815" }}>
                  Logged!
                </p>
              </div>
            ) : (
              <>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 16,
                  }}
                >
                  <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>Log a purchase</h3>
                  <button
                    type="button"
                    onClick={closeSheet}
                    aria-label="Close"
                    style={{
                      border: "none",
                      background: "transparent",
                      padding: 8,
                      cursor: "pointer",
                    }}
                  >
                    <X size={22} aria-hidden />
                  </button>
                </div>

                <label
                  htmlFor="quick-spend-amount"
                  style={{ fontSize: 13, fontWeight: 600, color: "#582C8E" }}
                >
                  How much?
                </label>
                <input
                  ref={amountRef}
                  id="quick-spend-amount"
                  type="number"
                  inputMode="decimal"
                  min={0}
                  step="0.01"
                  placeholder="$0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  style={{
                    width: "100%",
                    fontSize: 32,
                    fontWeight: 700,
                    border: "none",
                    borderBottom: "2px solid #E5E7EB",
                    padding: "8px 0 12px",
                    marginBottom: 20,
                    outline: "none",
                  }}
                />

                <p style={{ fontSize: 13, fontWeight: 600, color: "#582C8E", margin: "0 0 8px" }}>
                  Spend vibe
                </p>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 8,
                    marginBottom: 20,
                  }}
                >
                  {SPEND_VIBES.map((vibe) => {
                    const selected = selectedVibe?.id === vibe.id;
                    return (
                      <button
                        key={vibe.id}
                        type="button"
                        onClick={() => {
                          setSelectedVibe(vibe);
                          setSelectedGroup(
                            MERCHANT_GROUPS.find(
                              (g) => g.id === vibe.merchantPriority[0]
                            ) ?? null
                          );
                          setSelectedMerchant(null);
                        }}
                        style={{
                          minHeight: 52,
                          borderRadius: 12,
                          border: selected ? "2px solid #582C8E" : "1px solid #E5E7EB",
                          background: selected ? "rgba(88,44,142,0.1)" : "#FAFAFA",
                          display: "flex",
                          alignItems: "center",
                          gap: 8,
                          padding: "8px 10px",
                          cursor: "pointer",
                          textAlign: "left",
                          fontSize: 13,
                          fontWeight: selected ? 700 : 500,
                        }}
                      >
                        <span aria-hidden>{vibe.emoji}</span>
                        <span>{vibe.label}</span>
                      </button>
                    );
                  })}
                </div>

                {selectedVibe && (
                  <>
                    <p
                      style={{
                        fontSize: 13,
                        fontWeight: 600,
                        color: "#582C8E",
                        margin: "0 0 8px",
                      }}
                    >
                      Merchant (optional)
                    </p>
                    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                      {sortedGroups.map((group) => (
                        <div key={group.id}>
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedGroup(group);
                              setSelectedMerchant(null);
                            }}
                            style={{
                              width: "100%",
                              textAlign: "left",
                              padding: "10px 12px",
                              borderRadius: 10,
                              border:
                                selectedGroup?.id === group.id
                                  ? "2px solid #582C8E"
                                  : "1px solid #E5E7EB",
                              background:
                                selectedGroup?.id === group.id
                                  ? "rgba(88,44,142,0.08)"
                                  : "#fff",
                              fontWeight: 600,
                              fontSize: 13,
                              cursor: "pointer",
                              marginBottom: 6,
                            }}
                          >
                            {group.label}
                          </button>
                          {selectedGroup?.id === group.id && (
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                              {group.merchants.map((merchant) => {
                                const mSelected = selectedMerchant?.id === merchant.id;
                                return (
                                  <button
                                    key={merchant.id}
                                    type="button"
                                    onClick={() => setSelectedMerchant(merchant)}
                                    style={{
                                      padding: "6px 10px",
                                      borderRadius: 999,
                                      border: mSelected
                                        ? "2px solid #582C8E"
                                        : "1px solid #D1D5DB",
                                      background: mSelected ? "#582C8E" : "#fff",
                                      color: mSelected ? "#fff" : "#374151",
                                      fontSize: 12,
                                      cursor: "pointer",
                                    }}
                                  >
                                    {merchant.name}
                                  </button>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </>
                )}

                {saveError && (
                  <p
                    role="alert"
                    style={{ color: "#DC2626", fontSize: 13, margin: "16px 0 0" }}
                  >
                    {saveError}
                  </p>
                )}

                <button
                  type="button"
                  data-testid="quick-spend-save"
                  disabled={!canSave}
                  onClick={handleSave}
                  style={{
                    width: "100%",
                    marginTop: 24,
                    minHeight: 48,
                    borderRadius: 14,
                    border: "none",
                    background: canSave ? "#582C8E" : "#D1D5DB",
                    color: "#fff",
                    fontWeight: 700,
                    fontSize: 16,
                    cursor: canSave ? "pointer" : "not-allowed",
                  }}
                >
                  {saving ? "Saving…" : "Save spend"}
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default MingusQuickSpend;
