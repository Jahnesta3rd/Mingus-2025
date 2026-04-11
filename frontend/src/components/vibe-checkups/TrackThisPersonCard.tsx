import { useCallback, useEffect, useState } from 'react';
import { useVibeTracker } from '../../hooks/useVibeTracker';

const QUICK_EMOJIS = ['💑', '👀', '🤔', '✨', '🚩', '💛'] as const;

type Mode = 'new' | 'existing';

export type TrackThisPersonCardProps = {
  leadId: string;
  onTracked: (personId: string) => void;
  onSkip: () => void;
};

export function TrackThisPersonCard({ leadId, onTracked, onSkip }: TrackThisPersonCardProps) {
  const { data, loading, error, getPeople, createPerson, linkAssessment } = useVibeTracker();
  const [mode, setMode] = useState<Mode>('new');
  const [nickname, setNickname] = useState('');
  const [pickedEmoji, setPickedEmoji] = useState<string | null>(null);
  const [customEmoji, setCustomEmoji] = useState('');
  const [selectedPersonId, setSelectedPersonId] = useState('');
  const [successNickname, setSuccessNickname] = useState<string | null>(null);
  const [actionBusy, setActionBusy] = useState(false);

  useEffect(() => {
    void getPeople().catch(() => {
      /* error surfaced via hook */
    });
  }, [getPeople]);

  const effectiveEmoji = (customEmoji.trim() || pickedEmoji || '').slice(0, 8) || null;

  const onStartTracking = useCallback(async () => {
    const nick = nickname.trim();
    if (!nick || actionBusy) return;
    setActionBusy(true);
    try {
      const created = await createPerson(nick, effectiveEmoji);
      await linkAssessment(created.person.id, leadId);
      setSuccessNickname(created.person.nickname);
      onTracked(created.person.id);
    } catch {
      /* error on hook */
    } finally {
      setActionBusy(false);
    }
  }, [actionBusy, createPerson, effectiveEmoji, leadId, linkAssessment, nickname, onTracked]);

  const onAddToHistory = useCallback(async () => {
    if (!selectedPersonId || actionBusy) return;
    setActionBusy(true);
    try {
      await linkAssessment(selectedPersonId, leadId);
      const p = data?.find((x) => x.id === selectedPersonId);
      setSuccessNickname(p?.nickname ?? 'this person');
      onTracked(selectedPersonId);
    } catch {
      /* error on hook */
    } finally {
      setActionBusy(false);
    }
  }, [actionBusy, data, leadId, linkAssessment, onTracked, selectedPersonId]);

  if (successNickname) {
    return (
      <div className="rounded-2xl border border-[#A78BFA]/55 bg-[#A78BFA]/12 px-5 py-6 text-center shadow-[0_0_28px_rgba(167,139,250,0.12)]">
        <p className="font-display text-base font-medium text-[#f0e8d8]">
          Added to {successNickname}&apos;s checkup history ✓
        </p>
        <a
          href="/dashboard/roster"
          className="mt-4 inline-block text-sm font-semibold text-[#A78BFA] underline-offset-2 hover:underline"
        >
          View their tracker
        </a>
      </div>
    );
  }

  const busy = loading || actionBusy;
  const people = data ?? [];

  return (
    <div className="rounded-2xl border border-[#2a2030] bg-[#1a1520]/80 px-5 py-6 text-left shadow-landing-card">
      {mode === 'new' ? (
        <>
          <h3 className="font-display text-center text-base font-semibold text-[#f0e8d8]">
            Track this person over time?
          </h3>
          <p className="mt-2 text-center text-sm text-[#f0e8d8]/85">
            Give them a nickname — only you can see this.
          </p>

          <div className="mt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-[#9a8f7e]">Emoji</p>
            <div className="mt-2 flex flex-wrap justify-center gap-2">
              {QUICK_EMOJIS.map((e) => (
                <button
                  key={e}
                  type="button"
                  aria-label={`Pick emoji ${e}`}
                  onClick={() => {
                    setPickedEmoji(e);
                    setCustomEmoji('');
                  }}
                  className={`rounded-lg border px-2.5 py-1.5 text-xl leading-none transition ${
                    pickedEmoji === e && !customEmoji.trim()
                      ? 'border-[#C4A064] bg-[#C4A064]/15'
                      : 'border-[#2a2030] bg-[#1a1520] hover:border-[#C4A064]/40'
                  }`}
                >
                  {e}
                </button>
              ))}
            </div>
            <input
              type="text"
              value={customEmoji}
              onChange={(ev) => {
                setCustomEmoji(ev.target.value.slice(0, 8));
                setPickedEmoji(null);
              }}
              placeholder="Or type your own…"
              maxLength={8}
              className="mt-3 w-full rounded-xl border border-[#2a2030] bg-[#1a1520] px-4 py-2.5 text-sm text-[#f0e8d8] outline-none ring-[#C4A064]/40 placeholder:text-[#9a8f7e] focus:ring-2"
            />
          </div>

          <label className="mt-4 block text-xs font-medium uppercase tracking-wider text-[#9a8f7e]" htmlFor="vc-track-nickname">
            Nickname
          </label>
          <input
            id="vc-track-nickname"
            type="text"
            value={nickname}
            onChange={(e) => setNickname(e.target.value.slice(0, 30))}
            placeholder="e.g. Marcus, The Architect, Situationship..."
            maxLength={30}
            className="mt-2 w-full rounded-xl border border-[#2a2030] bg-[#1a1520] px-4 py-3 text-[#f0e8d8] outline-none ring-[#C4A064]/40 placeholder:text-[#9a8f7e] focus:ring-2"
          />

          {error ? <p className="mt-3 text-center text-sm text-rose-300">{error}</p> : null}

          <button
            type="button"
            disabled={busy || !nickname.trim()}
            onClick={() => void onStartTracking()}
            className="mt-5 w-full rounded-xl bg-[#C4A064] py-3.5 text-sm font-semibold text-[#0d0a08] shadow-landing-card transition hover:bg-[#d4b074] disabled:opacity-45"
          >
            {busy ? 'Saving…' : 'Start Tracking'}
          </button>

          <div className="mt-4 space-y-2 text-center">
            <button
              type="button"
              onClick={() => onSkip()}
              className="text-sm text-[#9a8f7e] underline-offset-2 hover:text-[#f0e8d8] hover:underline"
            >
              Skip for now
            </button>
            {people.length > 0 ? (
              <div>
                <button
                  type="button"
                  onClick={() => setMode('existing')}
                  className="text-sm font-medium text-[#C4A064] underline-offset-2 hover:underline"
                >
                  Someone I&apos;ve tracked
                </button>
              </div>
            ) : null}
          </div>
        </>
      ) : (
        <>
          <h3 className="font-display text-center text-base font-semibold text-[#f0e8d8]">
            Is this someone you&apos;ve assessed before?
          </h3>
          <label className="mt-4 block text-xs font-medium uppercase tracking-wider text-[#9a8f7e]" htmlFor="vc-track-existing">
            Tracked person
          </label>
          <select
            id="vc-track-existing"
            value={selectedPersonId}
            onChange={(e) => setSelectedPersonId(e.target.value)}
            className="mt-2 w-full rounded-xl border border-[#2a2030] bg-[#1a1520] px-4 py-3 text-[#f0e8d8] outline-none ring-[#C4A064]/40 focus:ring-2"
          >
            <option value="">Select…</option>
            {people.map((p) => (
              <option key={p.id} value={p.id}>
                {p.emoji ? `${p.emoji} ` : ''}
                {p.nickname}
              </option>
            ))}
          </select>

          {error ? <p className="mt-3 text-center text-sm text-rose-300">{error}</p> : null}

          <button
            type="button"
            disabled={busy || !selectedPersonId}
            onClick={() => void onAddToHistory()}
            className="mt-5 w-full rounded-xl bg-[#C4A064] py-3.5 text-sm font-semibold text-[#0d0a08] shadow-landing-card transition hover:bg-[#d4b074] disabled:opacity-45"
          >
            {busy ? 'Saving…' : 'Add to their history'}
          </button>

          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => setMode('new')}
              className="text-sm font-medium text-[#C4A064] underline-offset-2 hover:underline"
            >
              New person
            </button>
          </div>
        </>
      )}
    </div>
  );
}
