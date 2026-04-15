import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from './useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';
import type {
  ConvCluster,
  ConvMessage,
  ConvPhase,
  ExtractedData,
  ExtractedExpense,
  ExtractedIncome,
  ExtractedMilestone,
} from '../types/conversationalOnboarding';

const READY_TOKENS = ['[INCOME_READY]', '[EXPENSES_READY]', '[MILESTONES_READY]', '[CLUSTER_READY]'];

const INITIAL_EXTRACTED: ExtractedData = {
  income: null,
  expenses: [],
  milestones: [],
};

function stripClusterReadyTokens(text: string): string {
  let out = text;
  for (const tok of READY_TOKENS) {
    out = out.split(tok).join('');
  }
  return out.replace(/\s+/g, ' ').trim();
}

function newMessage(role: ConvMessage['role'], content: string): ConvMessage {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
    role,
    content,
    timestamp: Date.now(),
  };
}

function normalizeApiExtracted(
  cluster: ConvCluster,
  raw: unknown,
): Partial<ExtractedData> {
  if (!raw || typeof raw !== 'object') return {};
  const o = raw as Record<string, unknown>;
  if (cluster === 'income') {
    return { income: o as unknown as ExtractedIncome };
  }
  if (cluster === 'expenses' && Array.isArray(o.categories)) {
    return { expenses: o.categories as ExtractedExpense[] };
  }
  if (cluster === 'milestones' && Array.isArray(o.events)) {
    return { milestones: o.events as ExtractedMilestone[] };
  }
  return {};
}

function confirmPayloadForCluster(
  cluster: ConvCluster,
  edited: Partial<ExtractedData>,
): Record<string, unknown> {
  if (cluster === 'income') {
    return { ...(edited.income ?? {}) };
  }
  if (cluster === 'expenses') {
    return { categories: edited.expenses ?? [] };
  }
  if (cluster === 'milestones') {
    return { events: edited.milestones ?? [] };
  }
  return {};
}

function mergeExtracted(prev: ExtractedData, patch: Partial<ExtractedData>): ExtractedData {
  return {
    income: patch.income !== undefined ? patch.income : prev.income,
    expenses: patch.expenses !== undefined ? patch.expenses : prev.expenses,
    milestones: patch.milestones !== undefined ? patch.milestones : prev.milestones,
  };
}

const CLUSTER_INTROS: Record<string, string> = {
  expenses:
    "Great. Now let's talk about what goes out. What are your two biggest monthly expenses?",
  milestones:
    'Perfect. Last thing — is there anything coming up in the next few months that costs money? A trip, an event, a registration, anything like that?',
};

export function useConversationalOnboarding() {
  const { user, getAccessToken } = useAuth();
  const firstName = useMemo(() => {
    const n = user?.name?.trim();
    if (!n) return 'there';
    return n.split(/\s+/)[0] ?? 'there';
  }, [user?.name]);

  const [messages, setMessages] = useState<ConvMessage[]>([]);
  const [cluster, setCluster] = useState<ConvCluster>('income');
  const [phase, setPhase] = useState<ConvPhase>('chatting');
  const [extracted, setExtracted] = useState<ExtractedData>({ ...INITIAL_EXTRACTED });
  const [pendingExtraction, setPendingExtraction] = useState<Partial<ExtractedData> | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [turnCount, setTurnCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const authHeaders = useCallback((): Record<string, string> => {
    const token = getAccessToken();
    return {
      'Content-Type': 'application/json',
      ...csrfHeaders(),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }, [getAccessToken]);

  const openingText = useMemo(
    () =>
      `Hey ${firstName}. Let's get your finances set up. I'll ask you a few questions — it takes about 3 minutes. To start: what's your monthly take-home pay after taxes?`,
    [firstName],
  );

  useEffect(() => {
    setMessages((prev) => {
      if (prev.length > 0) return prev;
      return [newMessage('assistant', openingText)];
    });
  }, [openingText]);

  const sendMessage = useCallback(
    async (userText: string) => {
      setError(null);
      setMessages((prev) => [...prev, newMessage('user', userText)]);
      setIsTyping(true);

      try {
        const res = await fetch('/api/conversation-onboarding/message', {
          method: 'POST',
          credentials: 'include',
          headers: authHeaders(),
          body: JSON.stringify({ message: userText }),
        });

        const response = (await res.json().catch(() => ({}))) as Record<string, unknown>;
        setIsTyping(false);

        if (!res.ok) {
          const msg =
            (typeof response.error === 'string' && response.error) ||
            (typeof response.message === 'string' && response.message) ||
            `Request failed (${res.status})`;
          setError(msg);
          setPhase('error');
          return;
        }

        if (response.type === 'hard_cap') {
          const capText =
            typeof response.message === 'string'
              ? response.message
              : 'You have reached the conversation limit for this session.';
          setMessages((prev) => [...prev, newMessage('assistant', capText)]);
          setPhase('hard_cap');
          if (typeof response.turn === 'number') setTurnCount(response.turn);
          return;
        }

        const rawContent =
          typeof response.content === 'string' ? response.content : String(response.content ?? '');
        const displayContent = stripClusterReadyTokens(rawContent);
        setMessages((prev) => [...prev, newMessage('assistant', displayContent)]);

        if (typeof response.turn === 'number') setTurnCount(response.turn);

        const currentCluster = (response.cluster as ConvCluster) || cluster;
        if (response.ready_to_confirm === true && response.extracted != null) {
          setPendingExtraction(normalizeApiExtracted(currentCluster, response.extracted));
          setPhase('confirming');
        }
      } catch (e) {
        setIsTyping(false);
        const msg = e instanceof Error ? e.message : 'Network error';
        setError(msg);
        setPhase('error');
      }
    },
    [authHeaders, cluster],
  );

  const confirmCluster = useCallback(
    async (editedData: Partial<ExtractedData>) => {
      setError(null);
      setPhase('confirmed');
      setExtracted((prev) => mergeExtracted(prev, editedData));

      try {
        const res = await fetch('/api/conversation-onboarding/confirm', {
          method: 'POST',
          credentials: 'include',
          headers: authHeaders(),
          body: JSON.stringify({
            cluster,
            data: confirmPayloadForCluster(cluster, editedData),
          }),
        });

        const response = (await res.json().catch(() => ({}))) as Record<string, unknown>;

        if (!res.ok) {
          const msg =
            (typeof response.error === 'string' && response.error) ||
            `Request failed (${res.status})`;
          setError(msg);
          setPhase('error');
          return;
        }

        const nextCluster = response.next_cluster as ConvCluster;
        setCluster(nextCluster);
        setPendingExtraction(null);

        if (response.done === true) {
          setPhase('committing');
          queueMicrotask(() => setPhase('complete'));
          return;
        }

        setPhase('chatting');
        const intro = CLUSTER_INTROS[nextCluster];
        if (intro) {
          setMessages((prev) => [...prev, newMessage('assistant', intro)]);
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Network error';
        setError(msg);
        setPhase('error');
      }
    },
    [authHeaders, cluster],
  );

  const resetConversation = useCallback(async () => {
    setError(null);
    try {
      const res = await fetch('/api/conversation-onboarding/reset', {
        method: 'DELETE',
        credentials: 'include',
        headers: authHeaders(),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as Record<string, unknown>;
        const msg =
          (typeof body.error === 'string' && body.error) || `Request failed (${res.status})`;
        setError(msg);
        setPhase('error');
        return;
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Network error';
      setError(msg);
      setPhase('error');
      return;
    }

    setMessages([newMessage('assistant', openingText)]);
    setCluster('income');
    setPhase('chatting');
    setExtracted({ ...INITIAL_EXTRACTED });
    setPendingExtraction(null);
    setIsTyping(false);
    setTurnCount(0);
  }, [authHeaders, openingText]);

  return {
    messages,
    cluster,
    phase,
    extracted,
    pendingExtraction,
    isTyping,
    turnCount,
    error,
    sendMessage,
    confirmCluster,
    resetConversation,
  };
}
