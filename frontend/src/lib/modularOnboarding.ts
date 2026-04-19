import { csrfHeaders } from '../utils/csrfHeaders';
import type {
  CommitFieldResponse,
  CommitModuleResponse,
  MessageResponse,
  ModuleData,
  ModuleId,
  RevisitModuleResponse,
  SkipModuleResponse,
  StatusResponse,
} from '../types/modularOnboarding';
import { MODULE_ORDER } from '../types/modularOnboarding';

const BASE = '/api/modular-onboarding';

export type ModularOnboardingRequestError = Error & {
  status?: number;
  body?: unknown;
};

function isModuleId(value: string): value is ModuleId {
  return (MODULE_ORDER as readonly string[]).includes(value);
}

function filterModuleIds(values: unknown): ModuleId[] {
  if (!Array.isArray(values)) return [];
  const out: ModuleId[] = [];
  for (const v of values) {
    if (typeof v === 'string' && isModuleId(v)) out.push(v);
  }
  return out;
}

function uniqueModuleIds(lists: ModuleId[][]): ModuleId[] {
  const seen = new Set<ModuleId>();
  const out: ModuleId[] = [];
  for (const list of lists) {
    for (const id of list) {
      if (!seen.has(id)) {
        seen.add(id);
        out.push(id);
      }
    }
  }
  return out;
}

/** Raw envelope from GET /api/modular-onboarding/status (Flask). */
interface StatusApiEnvelope {
  session?: {
    current_module?: string;
    completed_modules?: unknown;
    skipped_modules?: unknown;
    turn_count?: number;
  };
  db?: {
    is_complete?: boolean;
    current_module?: string;
    completed_modules?: unknown;
    skipped_modules?: unknown;
  } | null;
}

function sessionIsComplete(
  completed: ModuleId[],
  skipped: ModuleId[]
): boolean {
  const seen = new Set<ModuleId>([...completed, ...skipped]);
  return MODULE_ORDER.every((id) => seen.has(id));
}

/** Maps the backend status JSON to the flat StatusResponse used by the hook. */
function normalizeStatusPayload(raw: unknown): StatusResponse {
  const env = raw as StatusApiEnvelope;
  const session = env.session ?? {};
  const db = env.db;

  const completedFromSession = filterModuleIds(session.completed_modules);
  const skippedFromSession = filterModuleIds(session.skipped_modules);
  const completedFromDb = db ? filterModuleIds(db.completed_modules) : [];
  const skippedFromDb = db ? filterModuleIds(db.skipped_modules) : [];

  // Union: Redis payload may omit lists while DB row still has resume flags.
  const completed_modules = uniqueModuleIds([
    completedFromSession,
    completedFromDb,
  ]);
  const skipped_modules = uniqueModuleIds([skippedFromSession, skippedFromDb]);

  const cmRaw =
    (typeof session.current_module === 'string' && session.current_module) ||
    (typeof db?.current_module === 'string' && db.current_module) ||
    null;
  const current_module = cmRaw && isModuleId(cmRaw) ? cmRaw : null;

  const turn_count =
    typeof session.turn_count === 'number' ? session.turn_count : 0;

  const is_complete =
    typeof db?.is_complete === 'boolean'
      ? db.is_complete
      : sessionIsComplete(completed_modules, skipped_modules);

  return {
    current_module,
    completed_modules,
    skipped_modules,
    turn_count,
    is_complete,
    data: {},
  };
}

async function readJsonBody(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return {};
  }
}

function throwHttpError(
  status: number,
  body: Record<string, unknown>
): never {
  if (status === 401) {
    try {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('mingus_token');
    } catch {
      /* ignore */
    }
    const err = new Error('UNAUTHORIZED') as ModularOnboardingRequestError;
    err.status = 401;
    err.body = body;
    throw err;
  }
  const msg = `${status}: ${String(body.error ?? body.message ?? 'request failed')}`;
  const err = new Error(msg) as ModularOnboardingRequestError;
  err.status = status;
  err.body = body;
  throw err;
}

async function requestJson<T>(
  method: string,
  path: string,
  token: string,
  body?: unknown
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
    ...csrfHeaders(),
  };

  const res = await fetch(path, {
    method,
    credentials: 'include',
    headers,
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });

  const parsed = (await readJsonBody(res)) as Record<string, unknown>;

  if (!res.ok) {
    throwHttpError(res.status, parsed);
  }

  return parsed as T;
}

export async function sendMessage(
  token: string,
  userMessage: string,
  currentModuleId: ModuleId
): Promise<MessageResponse> {
  return requestJson<MessageResponse>('POST', `${BASE}/message`, token, {
    user_message: userMessage,
    current_module_id: currentModuleId,
  });
}

export async function commitField(
  token: string,
  moduleId: ModuleId,
  fieldPath: string,
  value: unknown
): Promise<CommitFieldResponse> {
  return requestJson<CommitFieldResponse>(
    'POST',
    `${BASE}/commit-field`,
    token,
    { module_id: moduleId, field_path: fieldPath, value }
  );
}

export async function commitModule(
  token: string,
  moduleId: ModuleId,
  data: ModuleData[ModuleId]
): Promise<CommitModuleResponse> {
  return requestJson<CommitModuleResponse>(
    'POST',
    `${BASE}/commit-module`,
    token,
    { module_id: moduleId, data }
  );
}

export async function getBridge(
  token: string,
  fromModule: ModuleId,
  toModule: ModuleId
): Promise<{ bridge_message: string; cached: boolean }> {
  const res = await fetch(`${BASE}/bridge`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...csrfHeaders(),
    },
    body: JSON.stringify({
      from_module: fromModule,
      to_module: toModule,
    }),
  });
  if (!res.ok) {
    throw new Error(`${res.status}: bridge request failed`);
  }
  return (await res.json()) as { bridge_message: string; cached: boolean };
}

export async function skipModule(
  token: string,
  moduleId: ModuleId
): Promise<SkipModuleResponse> {
  return requestJson<SkipModuleResponse>(
    'POST',
    `${BASE}/skip-module`,
    token,
    { module_id: moduleId }
  );
}

export async function revisitModule(
  token: string,
  moduleId: ModuleId
): Promise<RevisitModuleResponse> {
  return requestJson<RevisitModuleResponse>(
    'POST',
    `${BASE}/revisit-module`,
    token,
    { module_id: moduleId }
  );
}

export async function getStatus(token: string): Promise<StatusResponse> {
  const raw = await requestJson<unknown>('GET', `${BASE}/status`, token);
  return normalizeStatusPayload(raw);
}

export async function resetSession(token: string): Promise<{ ok: boolean }> {
  const raw = await requestJson<{ reset?: boolean; ok?: boolean }>(
    'DELETE',
    `${BASE}/reset`,
    token
  );
  if (raw && typeof raw === 'object' && raw.reset === true) {
    return { ok: true };
  }
  if (raw && typeof raw === 'object' && raw.ok === true) {
    return { ok: true };
  }
  return { ok: false };
}
