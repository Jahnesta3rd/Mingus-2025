import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from './useAuth';
import * as api from '../lib/modularOnboarding';
import type {
  CommitFieldResponse,
  OnboardingState,
  ModuleId,
  ModuleData,
  Message,
} from '../types/modularOnboarding';
import { MODULE_ORDER } from '../types/modularOnboarding';

// Module display names (keep in sync with backend MODULES registry):
const MODULE_DISPLAY_NAMES: Record<ModuleId, string> = {
  income: 'Income',
  housing: 'Housing',
  vehicle: 'Vehicle',
  recurring_expenses: 'Recurring Expenses',
  roster: 'Vibe Check',
  career: 'Career',
  milestones: 'Milestones',
};

const NEW_ROW_PATH_RE = /^(vehicles|people|events)\[new\]\.([a-z_]+)$/;

function greetingFirstName(userName: string | null | undefined): string | null {
  if (!userName?.trim()) return null;
  const part = userName.trim().split(/\s+/)[0];
  return part || null;
}

// INITIAL_STATE factory — accepts firstName for the opening message.
// Default module order: income is 'active', rest 'pending'.
function buildInitialState(firstName: string | null): OnboardingState {
  const name = firstName || 'there';
  const openingMessage: Message = {
    id: 'opening-' + Date.now(),
    role: 'assistant',
    content:
      `Hey ${name}. We are going to map out your finances in seven ` +
      `quick chunks. Your answers show up on the right as chips you ` +
      `can edit any time. Skip any module and come back to it, or tap ` +
      `any chip to change it. Ready? Let us start with what comes in.`,
    timestamp: Date.now(),
  };
  const modules = {} as OnboardingState['modules'];
  MODULE_ORDER.forEach((id, order) => {
    modules[id] = {
      id,
      order,
      display_name: MODULE_DISPLAY_NAMES[id],
      status: order === 0 ? 'active' : 'pending',
    };
  });
  return {
    modules,
    currentModule: 'income',
    data: {
      income: {},
      housing: {},
      vehicle: { vehicle_count: 0, vehicles: [] },
      recurring_expenses: { categories: {} },
      roster: { people: [] },
      career: {},
      milestones: { events: [] },
    },
    messages: [openingMessage],
    isTyping: false,
    inputHint: null,
    phase: 'chatting',
    error: null,
    turnCount: 0,
  };
}

export function useModularOnboarding() {
  const { getAccessToken, user, userTier } = useAuth();
  const token = getAccessToken();
  const firstName = greetingFirstName(user?.name);

  const [state, setState] = useState<OnboardingState>(() =>
    buildInitialState(firstName)
  );

  // On mount: hydrate from backend if user is resuming.
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    void (async () => {
      try {
        const status = await api.getStatus(token);
        if (cancelled) return;
        // Merge backend state into local state without overwriting the
        // opening message. Updated modules reflect backend completion.
        setState((prev) => ({
          ...prev,
          currentModule: status.current_module,
          turnCount: status.turn_count,
          data: { ...prev.data, ...status.data } as ModuleData,
          modules: MODULE_ORDER.reduce((acc, id, order) => {
            let status_: OnboardingState['modules'][ModuleId]['status'];
            if (status.completed_modules.includes(id)) status_ = 'complete';
            else if (status.skipped_modules.includes(id)) status_ = 'skipped';
            else if (id === status.current_module) status_ = 'active';
            else status_ = 'pending';
            acc[id] = {
              id,
              order,
              display_name: MODULE_DISPLAY_NAMES[id],
              status: status_,
            };
            return acc;
          }, {} as OnboardingState['modules']),
          phase: status.is_complete ? 'complete' : 'chatting',
        }));
      } catch {
        // No existing session — initial state is fine.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  // sendUserMessage: optimistic user-message append, API call, phase handling.
  // CRITICAL: if text === '__module_start__' (sentinel from GC6), do NOT
  // append a user message to state.messages. Just set isTyping, call the
  // API, and let the assistant response land.
  const sendUserMessage = useCallback(
    async (text: string) => {
      if (!token || !state.currentModule) return;
      const isSentinel = text === '__module_start__';
      setState((prev) => ({
        ...prev,
        messages: isSentinel
          ? prev.messages
          : [
              ...prev.messages,
              {
                id: 'user-' + Date.now(),
                role: 'user',
                content: text,
                timestamp: Date.now(),
              },
            ],
        isTyping: true,
        inputHint: null,
      }));
      try {
        const resp = await api.sendMessage(token, text, state.currentModule);
        setState((prev) => ({
          ...prev,
          isTyping: false,
          messages: resp.assistant_message
            ? [
                ...prev.messages,
                {
                  id: 'assistant-' + Date.now(),
                  role: 'assistant',
                  content: resp.assistant_message,
                  timestamp: Date.now(),
                  inputHint: resp.detected_input_mode,
                },
              ]
            : prev.messages,
          inputHint: resp.detected_input_mode ?? null,
          phase: resp.phase,
          turnCount: prev.turnCount + 1,
          data:
            resp.phase === 'ready_to_commit' && resp.module && resp.extracted
              ? {
                  ...prev.data,
                  [resp.module]: {
                    ...prev.data[resp.module],
                    ...resp.extracted,
                  },
                }
              : prev.data,
        }));
      } catch (err) {
        setState((prev) => ({
          ...prev,
          isTyping: false,
          phase: 'error',
          error: err instanceof Error ? err.message : 'Network error',
        }));
      }
    },
    [token, state.currentModule]
  );

  // commitField: optimistic local update, API call, revert on 400.
  const commitField = useCallback(
    async (moduleId: ModuleId, fieldPath: string, value: unknown) => {
      if (!token) return;
      const snapshot = state.data;
      // Optimistic: merge locally. The shape of the merge depends on
      // fieldPath — dotted paths (e.g. 'monthly_takehome') vs indexed
      // paths (e.g. 'vehicles[0].make'). For GC3, implement the flat
      // case only; indexed paths use the backend's [new]/[i] semantics
      // and the local state update for those arrives via the commit
      // response assigned_index. Start simple: only flat paths update
      // optimistically. Indexed paths wait for the response.
      const isFlat = !/[\[\].]/.test(fieldPath);
      if (isFlat) {
        setState((prev) => ({
          ...prev,
          data: {
            ...prev.data,
            [moduleId]: {
              ...prev.data[moduleId],
              [fieldPath]: value,
            },
          },
          error: null,
        }));
      }
      try {
        const resp: CommitFieldResponse = await api.commitField(
          token,
          moduleId,
          fieldPath,
          value
        );

        if (resp.assigned_index != null && typeof resp.assigned_index === 'number') {
          const m = fieldPath.match(NEW_ROW_PATH_RE);
          if (m) {
            const arrSeg = m[1] as 'vehicles' | 'people' | 'events';
            const fieldKey = m[2];
            const target:
              | { mod: ModuleId; key: 'vehicles' | 'people' | 'events' }
              | undefined =
              arrSeg === 'vehicles'
                ? { mod: 'vehicle', key: 'vehicles' }
                : arrSeg === 'people'
                  ? { mod: 'roster', key: 'people' }
                  : { mod: 'milestones', key: 'events' };
            if (target && moduleId === target.mod) {
              const idx = resp.assigned_index;
              const stored =
                resp.value_stored !== undefined ? resp.value_stored : value;
              setState((prev) => {
                const d = prev.data;
                if (target.key === 'vehicles') {
                  const v = d.vehicle;
                  const list = [...(v.vehicles ?? [])];
                  while (list.length < idx + 1) {
                    list.push({});
                  }
                  const prevRow = list[idx] ?? {};
                  list[idx] = { ...prevRow, [fieldKey]: stored };
                  return {
                    ...prev,
                    error: null,
                    data: {
                      ...d,
                      vehicle: { ...v, vehicles: list },
                    },
                  };
                }
                if (target.key === 'people') {
                  const r = d.roster;
                  const list = [...(r.people ?? [])];
                  while (list.length < idx + 1) {
                    list.push({});
                  }
                  const prevRow = list[idx] ?? {};
                  list[idx] = { ...prevRow, [fieldKey]: stored };
                  return {
                    ...prev,
                    error: null,
                    data: {
                      ...d,
                      roster: { ...r, people: list },
                    },
                  };
                }
                const ms = d.milestones;
                const list = [...(ms.events ?? [])];
                while (list.length < idx + 1) {
                  list.push({});
                }
                const prevRow = list[idx] ?? {};
                list[idx] = { ...prevRow, [fieldKey]: stored };
                return {
                  ...prev,
                  error: null,
                  data: {
                    ...d,
                    milestones: { ...ms, events: list },
                  },
                };
              });
            }
          }
        }

        // On success, leave optimistic state as-is. Clear error.
        return resp;
      } catch (err) {
        const status =
          err && typeof err === 'object' && 'status' in err
            ? (err as api.ModularOnboardingRequestError).status
            : undefined;
        const isValidation =
          status === 400 &&
          err &&
          typeof err === 'object' &&
          'body' in err &&
          (err as api.ModularOnboardingRequestError).body &&
          typeof (err as api.ModularOnboardingRequestError).body === 'object' &&
          ((err as api.ModularOnboardingRequestError).body as { error?: string })
            .error === 'validation_failed';

        if (isFlat && isValidation) {
          setState((prev) => ({ ...prev, data: snapshot }));
        }
        const msg = err instanceof Error ? err.message : 'Commit failed';
        setState((prev) => ({ ...prev, error: msg }));
        throw err;
      }
    },
    [token, state.data]
  );

  // commitCurrentModule: called when user confirms the canvas.
  const commitCurrentModule = useCallback(async () => {
    if (!token || !state.currentModule) return;
    const moduleId = state.currentModule;
    setState((prev) => ({ ...prev, phase: 'committing', error: null }));
    try {
      const resp = await api.commitModule(token, moduleId, state.data[moduleId]);
      setState((prev) => {
        const newModules = { ...prev.modules };
        newModules[moduleId] = {
          ...newModules[moduleId],
          status: 'complete',
        };
        if (resp.next_module) {
          newModules[resp.next_module] = {
            ...newModules[resp.next_module],
            status: 'active',
          };
        }
        return {
          ...prev,
          modules: newModules,
          currentModule: resp.next_module,
          phase: resp.all_done ? 'complete' : 'chatting',
        };
      });
      return resp;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Commit failed';
      setState((prev) => ({ ...prev, phase: 'error', error: msg }));
      throw err;
    }
  }, [token, state.currentModule, state.data]);

  const skipCurrentModule = useCallback(async () => {
    if (!token || !state.currentModule) return;
    const moduleId = state.currentModule;
    const resp = await api.skipModule(token, moduleId);
    setState((prev) => {
      const newModules = { ...prev.modules };
      newModules[moduleId] = {
        ...newModules[moduleId],
        status: 'skipped',
      };
      if (resp.next_module) {
        newModules[resp.next_module] = {
          ...newModules[resp.next_module],
          status: 'active',
        };
      }
      return {
        ...prev,
        modules: newModules,
        currentModule: resp.next_module,
        phase: resp.all_done ? 'complete' : 'chatting',
      };
    });
  }, [token, state.currentModule]);

  const revisitModule = useCallback(
    async (moduleId: ModuleId) => {
      if (!token) return;
      await api.revisitModule(token, moduleId);
      setState((prev) => {
        const newModules = { ...prev.modules };
        newModules[moduleId] = {
          ...newModules[moduleId],
          status: 'active',
        };
        return {
          ...prev,
          modules: newModules,
          currentModule: moduleId,
          messages: [
            ...prev.messages,
            {
              id: 'system-revisit-' + Date.now(),
              role: 'system',
              content: `Going back to ${MODULE_DISPLAY_NAMES[moduleId]}. What would you like to change?`,
              timestamp: Date.now(),
            },
          ],
        };
      });
    },
    [token]
  );

  // editChip: alias for commitField with an "Updated" toast semantic.
  // For GC3, behavior is identical to commitField. The toast UX lives
  // in the canvas component (GC4).
  const editChip = commitField;

  const resetAll = useCallback(async () => {
    if (!token) return;
    await api.resetSession(token);
    setState(buildInitialState(firstName));
  }, [token, firstName]);

  const completedCount = useMemo(
    () =>
      Object.values(state.modules).filter(
        (m) => m.status === 'complete' || m.status === 'skipped'
      ).length,
    [state.modules]
  );

  const progressPct = useMemo(() => (completedCount / 7) * 100, [completedCount]);

  return {
    ...state,
    firstName,
    userTier,
    completedCount,
    progressPct,
    sendUserMessage,
    commitField,
    commitCurrentModule,
    skipCurrentModule,
    revisitModule,
    editChip,
    resetAll,
  };
}
