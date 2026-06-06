import { csrfHeaders } from '../../utils/csrfHeaders';

export const RESUME_ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt'] as const;
export const RESUME_MAX_BYTES = 5 * 1024 * 1024;

export type CareerResumeUploadStatus =
  | 'idle'
  | 'uploading'
  | 'success'
  | 'parse_error'
  | 'network_error';

export interface CareerResumeParsed {
  title?: string | null;
  industry?: string | null;
  years_experience?: number;
  skills?: string[];
  confidence_score?: number;
}

export interface CareerResumeUploadResponse {
  success?: boolean;
  file_path?: string;
  parsed?: CareerResumeParsed;
  parse_error?: string;
  message?: string;
  raw_advanced_analytics?: Record<string, unknown>;
  error?: string;
}

export interface CareerResumePrefill {
  title?: string | null;
  employer?: string | null;
  industry?: string | null;
  yearsExperience?: number | string | null;
}

export interface CareerResumeFieldSnapshot {
  title?: string | null;
  employer?: string | null;
  industry?: string | null;
  yearsExperience?: number | string | null;
}

function extensionOf(filename: string): string {
  const idx = filename.lastIndexOf('.');
  return idx >= 0 ? filename.slice(idx).toLowerCase() : '';
}

export function validateResumeFile(file: File | null | undefined): string | null {
  if (!file) {
    return 'Please choose a resume file.';
  }
  const ext = extensionOf(file.name);
  if (!RESUME_ALLOWED_EXTENSIONS.includes(ext as (typeof RESUME_ALLOWED_EXTENSIONS)[number])) {
    return 'Invalid file type. Allowed types: .pdf, .docx, .doc, .txt';
  }
  if (file.size > RESUME_MAX_BYTES) {
    return 'File exceeds maximum size of 5MB';
  }
  return null;
}

function readString(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function readRecord(value: unknown): Record<string, unknown> | null {
  return value != null && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function readArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

/** Extract employer from parser payload when available. */
export function extractEmployerFromUploadResponse(
  response: CareerResumeUploadResponse
): string | null {
  const analytics = readRecord(response.raw_advanced_analytics);
  if (!analytics) return null;

  const contactInfo = readRecord(analytics.contact_info);
  const fromContact = readString(contactInfo?.company);
  if (fromContact) return fromContact;

  const experience = readArray(analytics.experience);
  const first = readRecord(experience[0]);
  return readString(first?.company);
}

export function buildPrefillFromUploadResponse(
  response: CareerResumeUploadResponse
): CareerResumePrefill {
  const parsed = response.parsed ?? {};
  return {
    title: readString(parsed.title),
    employer: extractEmployerFromUploadResponse(response),
    industry: readString(parsed.industry),
    yearsExperience:
      typeof parsed.years_experience === 'number' ? parsed.years_experience : null,
  };
}

export function hasNonEmptyParsed(parsed: CareerResumeParsed | undefined): boolean {
  if (!parsed) return false;
  if (readString(parsed.title)) return true;
  if (readString(parsed.industry)) return true;
  if (typeof parsed.years_experience === 'number' && parsed.years_experience > 0) {
    return true;
  }
  if (Array.isArray(parsed.skills) && parsed.skills.length > 0) return true;
  return false;
}

export async function uploadCareerResume(
  file: File,
  getAccessToken: () => string | null
): Promise<{ ok: true; data: CareerResumeUploadResponse } | { ok: false; kind: 'network' | 'validation'; data?: CareerResumeUploadResponse }> {
  const formData = new FormData();
  formData.append('resume', file);

  const headers: Record<string, string> = { ...csrfHeaders() };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch('/api/career/resume', {
      method: 'POST',
      credentials: 'include',
      headers,
      body: formData,
    });
  } catch {
    return { ok: false, kind: 'network' };
  }

  let data: CareerResumeUploadResponse = {};
  try {
    data = (await response.json()) as CareerResumeUploadResponse;
  } catch {
    if (!response.ok) {
      return { ok: false, kind: 'network' };
    }
  }

  if (response.status === 422 || !response.ok) {
    return { ok: false, kind: response.status === 422 ? 'validation' : 'network', data };
  }

  return { ok: true, data };
}

/** Apply parsed resume values without overwriting existing non-empty fields. */
export function applyResumePrefill(
  current: CareerResumeFieldSnapshot,
  prefill: CareerResumePrefill
): CareerResumeFieldSnapshot {
  const next: CareerResumeFieldSnapshot = { ...current };

  if (!readString(current.title) && readString(prefill.title)) {
    next.title = prefill.title;
  }
  if (!readString(current.employer) && readString(prefill.employer)) {
    next.employer = prefill.employer;
  }
  if (!readString(current.industry) && readString(prefill.industry)) {
    next.industry = prefill.industry;
  }

  const currentYears = current.yearsExperience;
  const yearsEmpty =
    currentYears == null ||
    currentYears === '' ||
    (typeof currentYears === 'number' && currentYears === 0) ||
    (typeof currentYears === 'string' && (currentYears === '' || currentYears === '0'));

  if (
    yearsEmpty &&
    typeof prefill.yearsExperience === 'number' &&
    prefill.yearsExperience >= 0
  ) {
    next.yearsExperience = prefill.yearsExperience;
  }

  return next;
}
