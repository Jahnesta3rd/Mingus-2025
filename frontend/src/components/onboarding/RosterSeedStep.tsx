import React, { useCallback, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { csrfHeaders } from '../../utils/csrfHeaders';

export type RosterCardType = 'person' | 'kids' | 'social';

export interface RosterSeedStepProps {
  onSubmitted: (firstPerson: { id: string; nickname: string }) => void;
  onSkip: () => void;
  setPageError: (msg: string | null) => void;
}

interface VibePersonPayload {
  id: string;
  nickname: string;
  card_type: string;
}

interface CreatePersonResponse {
  person: VibePersonPayload;
}

function buildHeaders(getAccessToken: () => string | null): HeadersInit {
  const h: Record<string, string> = { ...csrfHeaders(), 'Content-Type': 'application/json' };
  const token = getAccessToken();
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

async function readErrorMessage(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const j = JSON.parse(text) as { error?: string; message?: string };
    return j.error || j.message || text || res.statusText;
  } catch {
    return text || res.statusText || 'Request failed';
  }
}

const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-[#1E293B] placeholder:text-[#64748B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';
const labelClass = 'mb-1.5 block text-sm font-medium text-[#1E293B]';

const CARD_OPTIONS: { type: RosterCardType; label: string; emoji: string }[] = [
  { type: 'person', label: 'Dating/Seeing', emoji: '👤' },
  { type: 'kids', label: 'My child', emoji: '👶' },
  { type: 'social', label: 'Friend/Other', emoji: '👥' },
];

function CardTypeRow({
  value,
  onChange,
}: {
  value: RosterCardType;
  onChange: (t: RosterCardType) => void;
}) {
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {CARD_OPTIONS.map((opt) => {
        const active = value === opt.type;
        return (
          <button
            key={opt.type}
            type="button"
            onClick={() => onChange(opt.type)}
            aria-pressed={active}
            className={`min-h-11 min-w-0 flex-1 rounded-xl border px-3 py-2 text-left text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 ${
              active
                ? 'border-[#5B2D8E] bg-[#EDE9FE] text-[#5B2D8E]'
                : 'border-[#E2E8F0] bg-white text-[#64748B] hover:border-[#CBD5E1]'
            }`}
          >
            <span className="mr-1.5" aria-hidden>
              {opt.emoji}
            </span>
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

export default function RosterSeedStep({ onSubmitted, onSkip, setPageError }: RosterSeedStepProps) {
  const { getAccessToken } = useAuth();
  const [nick1, setNick1] = useState('');
  const [nick2, setNick2] = useState('');
  const [card1, setCard1] = useState<RosterCardType>('person');
  const [card2, setCard2] = useState<RosterCardType>('person');
  const [submitting, setSubmitting] = useState(false);

  const showSecond = nick1.trim().length > 0;

  const postPerson = useCallback(
    async (nickname: string, card_type: RosterCardType): Promise<VibePersonPayload> => {
      const name = nickname.trim();
      if (!name) {
        throw new Error('Nickname is required.');
      }
      const res = await fetch('/api/vibe-tracker/people', {
        method: 'POST',
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
        body: JSON.stringify({ nickname: name, card_type }),
      });
      if (res.status !== 201 && res.status !== 200) {
        throw new Error(await readErrorMessage(res));
      }
      const json = (await res.json()) as CreatePersonResponse;
      return json.person;
    },
    [getAccessToken]
  );

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPageError(null);
    const n1 = nick1.trim();
    if (!n1) {
      setPageError('Add at least one nickname or skip for now.');
      return;
    }
    setSubmitting(true);
    try {
      const first = await postPerson(n1, card1);
      const n2 = nick2.trim();
      if (n2.length > 0) {
        await postPerson(n2, card2);
      }
      onSubmitted({ id: first.id, nickname: first.nickname });
    } catch (err) {
      setPageError(err instanceof Error ? err.message : 'Could not add to roster');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">
          Who&apos;s on your mind right now?
        </h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Add 1 or 2 people you want to keep track of. Use a nickname — this is just for you.
        </p>

        <div className="mt-6 space-y-6">
          <div>
            <label className={labelClass} htmlFor="roster-nick-1">
              Add someone
            </label>
            <input
              id="roster-nick-1"
              className={inputClass}
              placeholder="e.g. Lex, Jordan, Mom"
              value={nick1}
              onChange={(e) => setNick1(e.target.value)}
              autoComplete="off"
            />
            <CardTypeRow value={card1} onChange={setCard1} />
          </div>

          {showSecond && (
            <div>
              <label className={labelClass} htmlFor="roster-nick-2">
                Add another (optional)
              </label>
              <input
                id="roster-nick-2"
                className={inputClass}
                placeholder="e.g. Lex, Jordan, Mom"
                value={nick2}
                onChange={(e) => setNick2(e.target.value)}
                autoComplete="off"
              />
              <CardTypeRow value={card2} onChange={setCard2} />
            </div>
          )}
        </div>
      </div>

      <button
        type="submit"
        disabled={submitting || !nick1.trim()}
        className="min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 disabled:opacity-50"
      >
        {submitting ? 'Adding…' : 'Add to my Roster →'}
      </button>

      <button
        type="button"
        onClick={() => {
          setPageError(null);
          onSkip();
        }}
        className="min-h-11 w-full rounded-lg text-center text-sm text-[#64748B] hover:text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2"
      >
        Skip for now
      </button>
    </form>
  );
}
