import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ChevronRight,
  ExternalLink,
  Loader2,
} from 'lucide-react';
import { useAuth, type AuthUserTier } from '../hooks/useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';
import CareerResumeUploadSection from './career/CareerResumeUploadSection';
import type { PercentileData } from './RecommendationTiers';

const INCOME_PERCENTILE_API = '/api/career/income-percentile';
const FINANCIAL_SETUP_INCOME_API = '/api/financial-setup/income';

type IncomeFrequency = 'weekly' | 'biweekly' | 'semimonthly' | 'monthly' | 'annual';

interface IncomeSourceRow {
  id: string;
  source_name: string;
  amount: number;
  frequency: IncomeFrequency;
  pay_day?: number | null;
}

interface YouTabProps {
  focusField?: 'zip_code' | 'income';
  onFocusConsumed?: () => void;
}

const INCOME_FREQUENCY_OPTIONS: { value: IncomeFrequency; label: string }[] = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'biweekly', label: 'Bi-weekly' },
  { value: 'semimonthly', label: 'Semi-monthly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'annual', label: 'Annually' },
];

function formatIncomeCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(amount);
}

function frequencyLabel(frequency: string): string {
  return INCOME_FREQUENCY_OPTIONS.find((option) => option.value === frequency)?.label ?? frequency;
}

const MINGUS_PURPLE = '#5B2D8E';
const DEEP_PURPLE = '#3b1f6e';
const WHISPER_PURPLE = '#FAF5FF';
const SLATE_TEXT = '#1E293B';
const MUTED_TEXT = '#64748B';
const GOLD_ACCENT = '#fbbf24';

/** Backend has no POST /api/auth/change-password yet (auth_endpoints.py). */
const CHANGE_PASSWORD_ENABLED = false;

interface UserProfileResponse {
  first_name?: string;
  last_name?: string;
  email?: string;
  tier?: string;
  zip_code?: string;
  zip?: string;
  name?: string;
  personal_info?: Record<string, unknown>;
  preferences?: Record<string, unknown>;
}

function buildHeaders(getAccessToken: () => string | null, json = false): HeadersInit {
  const h: Record<string, string> = { ...csrfHeaders() };
  if (json) {
    h['Content-Type'] = 'application/json';
  }
  const token = getAccessToken();
  if (token) {
    h.Authorization = `Bearer ${token}`;
  }
  return h;
}

function normalizeTier(raw: string | undefined | null): AuthUserTier {
  if (raw === 'professional') return 'professional';
  if (raw === 'mid_tier' || raw === 'mid') return 'mid_tier';
  return 'budget';
}

function tierLabel(tier: AuthUserTier): string {
  switch (tier) {
    case 'professional':
      return 'Professional ($100/mo)';
    case 'mid_tier':
      return 'Mid-Tier ($35/mo)';
    default:
      return 'Budget ($15/mo)';
  }
}

function initialsFromName(first: string, last: string, email: string): string {
  const f = first.trim();
  const l = last.trim();
  if (f && l) return `${f[0]}${l[0]}`.toUpperCase();
  if (f) return f.slice(0, 2).toUpperCase();
  if (email) return email.slice(0, 2).toUpperCase();
  return '?';
}

function parseZip(profile: UserProfileResponse): string {
  if (profile.zip_code) return String(profile.zip_code);
  if (profile.zip) return String(profile.zip);
  const pi = profile.personal_info;
  if (pi) {
    const z = pi.zip_code ?? pi.zipCode ?? pi.zip;
    if (z != null && String(z).trim()) return String(z);
  }
  return '';
}

function parseNames(
  profile: UserProfileResponse,
  authName: string | undefined
): { firstName: string; lastName: string } {
  const first = (profile.first_name ?? '').trim();
  const last = (profile.last_name ?? '').trim();
  if (first || last) {
    return { firstName: first, lastName: last };
  }
  if (profile.name?.trim()) {
    const parts = profile.name.trim().split(/\s+/);
    return {
      firstName: parts[0] ?? '',
      lastName: parts.slice(1).join(' '),
    };
  }
  if (authName?.trim()) {
    const parts = authName.trim().split(/\s+/);
    return {
      firstName: parts[0] ?? '',
      lastName: parts.slice(1).join(' '),
    };
  }
  return { firstName: '', lastName: '' };
}

interface SectionCardProps {
  title: string;
  children: React.ReactNode;
}

function SectionCard({ title, children }: SectionCardProps) {
  return (
    <section className="mb-4 rounded-xl border border-[#E9D5FF] bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-base font-semibold" style={{ color: SLATE_TEXT }}>
        {title}
      </h2>
      {children}
    </section>
  );
}

interface SettingsRowProps {
  label: string;
  comingSoon?: boolean;
  onClick?: () => void;
  href?: string;
  external?: boolean;
  mailto?: string;
  trailing?: React.ReactNode;
}

function SettingsRow({
  label,
  comingSoon = false,
  onClick,
  href,
  external,
  mailto,
  trailing,
}: SettingsRowProps) {
  const content = (
    <>
      <span
        className={`text-sm font-medium ${comingSoon ? 'text-[#64748B]' : ''}`}
        style={comingSoon ? undefined : { color: SLATE_TEXT }}
      >
        {label}
      </span>
      <div className="flex items-center gap-2">
        {trailing}
        {comingSoon ? (
          <span className="text-xs font-medium text-[#64748B]">Coming soon</span>
        ) : external ? (
          <ExternalLink className="h-4 w-4 text-[#64748B]" aria-hidden />
        ) : (
          <ChevronRight className="h-4 w-4 text-[#64748B]" aria-hidden />
        )}
      </div>
    </>
  );

  const rowClass = `flex w-full items-center justify-between rounded-lg px-1 py-3 text-left transition-colors ${
    comingSoon ? 'cursor-not-allowed opacity-70' : 'hover:bg-[#FAF5FF] cursor-pointer'
  }`;

  if (comingSoon) {
    return (
      <div className={rowClass} aria-disabled="true">
        {content}
      </div>
    );
  }

  if (mailto) {
    return (
      <a href={mailto} className={rowClass}>
        {content}
      </a>
    );
  }

  if (href) {
    return (
      <a
        href={href}
        className={rowClass}
        {...(external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
      >
        {content}
      </a>
    );
  }

  return (
    <button type="button" className={rowClass} onClick={onClick}>
      {content}
    </button>
  );
}

function HeaderSkeleton() {
  return (
    <div className="animate-pulse px-6 py-10">
      <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-white/20" />
      <div className="mx-auto mb-2 h-6 w-40 rounded bg-white/20" />
      <div className="mx-auto mb-3 h-4 w-52 rounded bg-white/15" />
      <div className="mx-auto h-6 w-32 rounded-full bg-white/15" />
    </div>
  );
}

const YouTab: React.FC<YouTabProps> = ({ focusField, onFocusConsumed }) => {
  const navigate = useNavigate();
  const { user, userTier, getAccessToken } = useAuth();
  const incomeSectionRef = useRef<HTMLElement | null>(null);
  const focusAppliedRef = useRef<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [zipCode, setZipCode] = useState('');
  const [tier, setTier] = useState<AuthUserTier>('budget');

  const [draftFirstName, setDraftFirstName] = useState('');
  const [draftLastName, setDraftLastName] = useState('');
  const [draftZipCode, setDraftZipCode] = useState('');

  const [editingField, setEditingField] = useState<'first_name' | 'last_name' | 'zip_code' | null>(
    null
  );
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [saveError, setSaveError] = useState<string | null>(null);

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [passwordStatus, setPasswordStatus] = useState<'idle' | 'saving' | 'error'>('idle');
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const [signingOut, setSigningOut] = useState(false);
  const [percentileData, setPercentileData] = useState<PercentileData | null>(null);

  const [incomeRows, setIncomeRows] = useState<IncomeSourceRow[]>([]);
  const [incomeLoading, setIncomeLoading] = useState(true);
  const [incomeLoadError, setIncomeLoadError] = useState(false);
  const [showAddIncomeForm, setShowAddIncomeForm] = useState(false);
  const [incomeLabel, setIncomeLabel] = useState('');
  const [incomeAmount, setIncomeAmount] = useState('');
  const [incomeFrequency, setIncomeFrequency] = useState<IncomeFrequency>('monthly');
  const [incomeSaveStatus, setIncomeSaveStatus] = useState<'idle' | 'saving' | 'error'>('idle');
  const [incomeSaveError, setIncomeSaveError] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/user/profile', {
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
      });
      if (!res.ok) {
        throw new Error('Failed to load profile');
      }
      const data = (await res.json()) as { profile?: UserProfileResponse };
      const profile = data.profile ?? {};
      const names = parseNames(profile, user?.name);
      const resolvedEmail = profile.email ?? user?.email ?? '';
      const resolvedTier = normalizeTier(profile.tier ?? userTier ?? user?.tier);
      const resolvedZip = parseZip(profile);

      setFirstName(names.firstName);
      setLastName(names.lastName);
      setDraftFirstName(names.firstName);
      setDraftLastName(names.lastName);
      setEmail(resolvedEmail);
      setZipCode(resolvedZip);
      setDraftZipCode(resolvedZip);
      setTier(resolvedTier);
    } catch {
      const names = parseNames({}, user?.name);
      setFirstName(names.firstName);
      setLastName(names.lastName);
      setDraftFirstName(names.firstName);
      setDraftLastName(names.lastName);
      setEmail(user?.email ?? '');
      setTier(userTier ?? normalizeTier(user?.tier));
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, user?.email, user?.name, user?.tier, userTier]);

  useEffect(() => {
    void fetchProfile();
  }, [fetchProfile]);

  useEffect(() => {
    let cancelled = false;

    const fetchPercentileData = async () => {
      try {
        const res = await fetch(INCOME_PERCENTILE_API, {
          credentials: 'include',
          headers: buildHeaders(getAccessToken),
        });
        if (!res.ok || cancelled) return;

        const data = (await res.json()) as PercentileData;
        if (!cancelled && data.status === 'ok') {
          setPercentileData(data);
        }
      } catch {
        /* silent */
      }
    };

    void fetchPercentileData();
    return () => {
      cancelled = true;
    };
  }, [getAccessToken]);

  const fetchIncome = useCallback(async () => {
    setIncomeLoading(true);
    setIncomeLoadError(false);
    try {
      const res = await fetch(FINANCIAL_SETUP_INCOME_API, {
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
      });
      if (!res.ok) {
        throw new Error('Failed to load income');
      }
      const data = (await res.json()) as { income?: IncomeSourceRow[] };
      setIncomeRows(Array.isArray(data.income) ? data.income : []);
    } catch {
      setIncomeRows([]);
      setIncomeLoadError(true);
    } finally {
      setIncomeLoading(false);
    }
  }, [getAccessToken]);

  useEffect(() => {
    void fetchIncome();
  }, [fetchIncome]);

  useEffect(() => {
    if (!focusField) {
      focusAppliedRef.current = null;
      return;
    }
    if (loading || focusAppliedRef.current === focusField) return;

    if (focusField === 'zip_code') {
      setEditingField('zip_code');
      window.requestAnimationFrame(() => {
        document.getElementById('you-zip_code')?.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        });
      });
    } else if (focusField === 'income') {
      setShowAddIncomeForm(true);
      window.requestAnimationFrame(() => {
        incomeSectionRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        });
      });
    }

    focusAppliedRef.current = focusField;
    onFocusConsumed?.();
  }, [focusField, loading, onFocusConsumed]);

  const resetIncomeForm = () => {
    setIncomeLabel('');
    setIncomeAmount('');
    setIncomeFrequency('monthly');
    setIncomeSaveError(null);
    setIncomeSaveStatus('idle');
  };

  const handleCancelIncomeForm = () => {
    setShowAddIncomeForm(false);
    resetIncomeForm();
  };

  const handleSaveIncome = async () => {
    const label = incomeLabel.trim();
    const amount = parseFloat(incomeAmount);
    if (!label) {
      setIncomeSaveStatus('error');
      setIncomeSaveError('Enter a label for this income source.');
      return;
    }
    if (!Number.isFinite(amount) || amount <= 0) {
      setIncomeSaveStatus('error');
      setIncomeSaveError('Enter an amount greater than zero.');
      return;
    }

    setIncomeSaveStatus('saving');
    setIncomeSaveError(null);

    const sources = [
      ...incomeRows.map((row) => ({
        source_name: row.source_name,
        amount: row.amount,
        frequency: row.frequency,
        pay_day: row.pay_day ?? null,
      })),
      {
        source_name: label,
        amount,
        frequency: incomeFrequency,
        pay_day: null,
      },
    ];

    try {
      const res = await fetch(FINANCIAL_SETUP_INCOME_API, {
        method: 'POST',
        credentials: 'include',
        headers: buildHeaders(getAccessToken, true),
        body: JSON.stringify({ sources }),
      });
      const data = (await res.json().catch(() => ({}))) as { error?: string; message?: string };
      if (!res.ok) {
        throw new Error(data.error || data.message || 'Could not save income');
      }

      await fetchIncome();
      setShowAddIncomeForm(false);
      resetIncomeForm();
      setIncomeSaveStatus('idle');
    } catch (err) {
      setIncomeSaveStatus('error');
      setIncomeSaveError(err instanceof Error ? err.message : 'Could not save income');
    }
  };

  const displayName = useMemo(() => {
    const full = [firstName, lastName].filter(Boolean).join(' ').trim();
    return full || user?.name || email || 'Your profile';
  }, [email, firstName, lastName, user?.name]);

  const initials = useMemo(
    () => initialsFromName(firstName, lastName, email),
    [email, firstName, lastName]
  );

  const hasProfileChanges =
    draftFirstName !== firstName || draftLastName !== lastName || draftZipCode !== zipCode;

  const handleSaveProfile = async () => {
    if (!hasProfileChanges) return;

    setSaveStatus('saving');
    setSaveError(null);

    const patch: Record<string, string> = {};
    if (draftFirstName !== firstName) patch.first_name = draftFirstName.trim();
    if (draftLastName !== lastName) patch.last_name = draftLastName.trim();
    if (draftZipCode !== zipCode) patch.zip_code = draftZipCode.trim();

    try {
      const res = await fetch('/api/user/profile', {
        method: 'PATCH',
        credentials: 'include',
        headers: buildHeaders(getAccessToken, true),
        body: JSON.stringify(patch),
      });
      const data = (await res.json().catch(() => ({}))) as {
        success?: boolean;
        error?: string;
        message?: string;
      };

      if (!res.ok || data.success === false) {
        throw new Error(data.error || data.message || 'Could not save profile');
      }

      setFirstName(draftFirstName.trim());
      setLastName(draftLastName.trim());
      setZipCode(draftZipCode.trim());
      setEditingField(null);
      setSaveStatus('saved');
      window.setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (err) {
      setSaveStatus('error');
      setSaveError(err instanceof Error ? err.message : 'Could not save profile');
    }
  };

  const handleFieldBlur = (field: 'first_name' | 'last_name' | 'zip_code') => {
    setEditingField(null);
    if (hasProfileChanges) {
      void handleSaveProfile();
    }
  };

  const handleChangePassword = async () => {
    if (!CHANGE_PASSWORD_ENABLED) return;

    setPasswordError(null);
    if (newPassword !== confirmNewPassword) {
      setPasswordStatus('error');
      setPasswordError('New passwords do not match');
      return;
    }
    if (newPassword.length < 8) {
      setPasswordStatus('error');
      setPasswordError('Password must be at least 8 characters');
      return;
    }

    setPasswordStatus('saving');
    try {
      const res = await fetch('/api/auth/change-password', {
        method: 'POST',
        credentials: 'include',
        headers: buildHeaders(getAccessToken, true),
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      const data = (await res.json().catch(() => ({}))) as { error?: string; message?: string };
      if (!res.ok) {
        throw new Error(data.error || data.message || 'Could not change password');
      }
      setShowPasswordForm(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
      setPasswordStatus('idle');
    } catch (err) {
      setPasswordStatus('error');
      setPasswordError(err instanceof Error ? err.message : 'Could not change password');
    }
  };

  const handleSignOut = async () => {
    setSigningOut(true);
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
        headers: { ...csrfHeaders() },
      });
    } catch {
      /* redirect regardless */
    } finally {
      try {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('mingus_token');
      } catch {
        /* ignore */
      }
      navigate('/login');
    }
  };

  const renderProfileField = (
    id: 'first_name' | 'last_name' | 'zip_code',
    label: string,
    value: string,
    draft: string,
    onDraftChange: (v: string) => void,
    readOnly = false
  ) => {
    const isEditing = !readOnly && editingField === id;

    return (
      <div className="border-b border-[#E9D5FF]/60 py-3 last:border-b-0">
        <label
          htmlFor={readOnly ? undefined : `you-${id}`}
          className="mb-1 block text-xs font-medium uppercase tracking-wide"
          style={{ color: MUTED_TEXT }}
        >
          {label}
        </label>
        {readOnly ? (
          <p className="text-sm" style={{ color: SLATE_TEXT }}>
            {value || '—'}
          </p>
        ) : isEditing ? (
          <input
            id={`you-${id}`}
            type="text"
            autoFocus
            value={draft}
            onChange={(e) => onDraftChange(e.target.value)}
            onBlur={() => handleFieldBlur(id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.currentTarget.blur();
              }
            }}
            className="w-full rounded-lg border border-[#E9D5FF] px-3 py-2 text-sm outline-none focus:border-[#5B2D8E] focus:ring-1 focus:ring-[#5B2D8E]"
            style={{ color: SLATE_TEXT }}
          />
        ) : (
          <button
            type="button"
            className="w-full text-left text-sm hover:text-[#5B2D8E]"
            style={{ color: draft || value ? SLATE_TEXT : MUTED_TEXT }}
            onClick={() => setEditingField(id)}
          >
            {draft || value || 'Tap to add'}
          </button>
        )}
      </div>
    );
  };

  return (
    <div
      className="min-h-[calc(100vh-8rem)]"
      style={{ backgroundColor: WHISPER_PURPLE, paddingBottom: 96 }}
    >
      {/* Section 1: Profile Header */}
      <header
        className="mb-4 w-full"
        style={{
          background: `linear-gradient(135deg, ${DEEP_PURPLE} 0%, ${MINGUS_PURPLE} 100%)`,
        }}
      >
        {loading ? (
          <HeaderSkeleton />
        ) : (
          <div className="flex flex-col items-center px-6 py-10 text-center text-white">
            <div
              className="mb-4 flex h-16 w-16 items-center justify-center rounded-full text-xl font-bold"
              style={{ backgroundColor: 'rgba(255,255,255,0.2)' }}
              aria-hidden
            >
              {initials}
            </div>
            <h1 className="mb-1 text-xl font-bold">{displayName}</h1>
            <p className="mb-3 text-sm text-white/80">{email}</p>
            <span
              className="inline-flex rounded-full px-3 py-1 text-xs font-bold backdrop-blur-[8px]"
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.92)',
                color: DEEP_PURPLE,
              }}
            >
              {tierLabel(tier)}
            </span>
          </div>
        )}
      </header>

      <div className="px-4">
        {/* Section 2: Profile */}
        <SectionCard title="Profile">
          {percentileData?.zip_missing && (
            <div className="mb-4 rounded-lg border border-[#E9D5FF] bg-[#FAF5FF] px-3 py-2.5 text-sm" style={{ color: SLATE_TEXT }}>
              <span>Add your zip code to see how your income compares in your local market.</span>{' '}
              <button
                type="button"
                className="font-semibold underline-offset-2 hover:underline"
                style={{ color: MINGUS_PURPLE }}
                onClick={() => setEditingField('zip_code')}
              >
                Add zip code
              </button>
            </div>
          )}
          {renderProfileField(
            'first_name',
            'First name',
            firstName,
            draftFirstName,
            setDraftFirstName
          )}
          {renderProfileField('last_name', 'Last name', lastName, draftLastName, setDraftLastName)}
          <div className="border-b border-[#E9D5FF]/60 py-3 last:border-b-0">
            <label
              className="mb-1 block text-xs font-medium uppercase tracking-wide"
              style={{ color: MUTED_TEXT }}
            >
              Email
            </label>
            <p className="text-sm" style={{ color: SLATE_TEXT }}>
              {email || '—'}
            </p>
          </div>
          {renderProfileField('zip_code', 'ZIP code', zipCode, draftZipCode, setDraftZipCode)}

          <div className="mt-4 flex items-center gap-3">
            <button
              type="button"
              onClick={() => void handleSaveProfile()}
              disabled={!hasProfileChanges || saveStatus === 'saving'}
              className="rounded-lg px-4 py-2 text-sm font-semibold text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
              style={{ backgroundColor: MINGUS_PURPLE }}
            >
              {saveStatus === 'saving' ? 'Saving…' : 'Save'}
            </button>
            {saveStatus === 'saved' && (
              <span className="text-sm font-medium text-green-600">Saved</span>
            )}
            {saveStatus === 'error' && saveError && (
              <span className="text-sm font-medium text-red-600">{saveError}</span>
            )}
          </div>
        </SectionCard>

        <section ref={incomeSectionRef} id="you-income-section">
          <SectionCard title="Income Sources">
            {incomeLoading ? (
              <div className="flex items-center gap-2 text-sm" style={{ color: MUTED_TEXT }}>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                Loading income sources…
              </div>
            ) : incomeLoadError ? (
              <p className="text-sm" style={{ color: SLATE_TEXT }}>
                Add income in the{' '}
                <Link
                  to="/dashboard/tools?tab=forecast"
                  className="font-semibold underline-offset-2 hover:underline"
                  style={{ color: MINGUS_PURPLE }}
                >
                  Forecast tab
                </Link>
                .
              </p>
            ) : (
              <>
                {incomeRows.length === 0 ? (
                  <p className="mb-4 text-sm" style={{ color: MUTED_TEXT }}>
                    No income sources yet. Add your take-home pay to see percentile standing on job
                    recommendations.
                  </p>
                ) : (
                  <ul className="mb-4 divide-y divide-[#E9D5FF]/60 rounded-lg border border-[#E9D5FF]/60">
                    {incomeRows.map((row) => (
                      <li
                        key={row.id}
                        className="flex items-center justify-between gap-3 px-3 py-3 text-sm"
                      >
                        <span className="font-medium" style={{ color: SLATE_TEXT }}>
                          {row.source_name}
                        </span>
                        <span style={{ color: MUTED_TEXT }}>
                          {formatIncomeCurrency(row.amount)} · {frequencyLabel(row.frequency)}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}

                {showAddIncomeForm ? (
                  <div className="space-y-3 rounded-lg border border-[#E9D5FF] bg-[#FAF5FF] p-4">
                    <div>
                      <label htmlFor="you-income-label" className="mb-1 block text-xs font-medium uppercase tracking-wide" style={{ color: MUTED_TEXT }}>
                        Label
                      </label>
                      <input
                        id="you-income-label"
                        type="text"
                        value={incomeLabel}
                        onChange={(e) => setIncomeLabel(e.target.value)}
                        placeholder="e.g. Primary Salary"
                        className="w-full rounded-lg border border-[#E9D5FF] px-3 py-2 text-sm outline-none focus:border-[#5B2D8E] focus:ring-1 focus:ring-[#5B2D8E]"
                        style={{ color: SLATE_TEXT }}
                      />
                    </div>
                    <div>
                      <label htmlFor="you-income-amount" className="mb-1 block text-xs font-medium uppercase tracking-wide" style={{ color: MUTED_TEXT }}>
                        Amount
                      </label>
                      <input
                        id="you-income-amount"
                        type="number"
                        min="0"
                        step="0.01"
                        value={incomeAmount}
                        onChange={(e) => setIncomeAmount(e.target.value)}
                        placeholder="Monthly take-home"
                        className="w-full rounded-lg border border-[#E9D5FF] px-3 py-2 text-sm outline-none focus:border-[#5B2D8E] focus:ring-1 focus:ring-[#5B2D8E]"
                        style={{ color: SLATE_TEXT }}
                      />
                    </div>
                    <div>
                      <label htmlFor="you-income-frequency" className="mb-1 block text-xs font-medium uppercase tracking-wide" style={{ color: MUTED_TEXT }}>
                        Frequency
                      </label>
                      <select
                        id="you-income-frequency"
                        value={incomeFrequency}
                        onChange={(e) => setIncomeFrequency(e.target.value as IncomeFrequency)}
                        className="w-full rounded-lg border border-[#E9D5FF] px-3 py-2 text-sm outline-none focus:border-[#5B2D8E] focus:ring-1 focus:ring-[#5B2D8E]"
                        style={{ color: SLATE_TEXT }}
                      >
                        {INCOME_FREQUENCY_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    {incomeSaveStatus === 'error' && incomeSaveError && (
                      <p className="text-sm text-red-600">{incomeSaveError}</p>
                    )}
                    <div className="flex flex-wrap gap-2 pt-1">
                      <button
                        type="button"
                        onClick={() => void handleSaveIncome()}
                        disabled={incomeSaveStatus === 'saving'}
                        className="rounded-lg px-4 py-2 text-sm font-semibold text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
                        style={{ backgroundColor: MINGUS_PURPLE }}
                      >
                        {incomeSaveStatus === 'saving' ? 'Saving…' : 'Save'}
                      </button>
                      <button
                        type="button"
                        onClick={handleCancelIncomeForm}
                        disabled={incomeSaveStatus === 'saving'}
                        className="rounded-lg border border-[#E9D5FF] px-4 py-2 text-sm font-medium"
                        style={{ color: SLATE_TEXT }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setShowAddIncomeForm(true)}
                    className="rounded-lg border border-[#E9D5FF] px-4 py-2 text-sm font-semibold transition-colors hover:bg-[#FAF5FF]"
                    style={{ color: MINGUS_PURPLE }}
                  >
                    Add income source
                  </button>
                )}
              </>
            )}
          </SectionCard>
        </section>

        {/* Section 3: Resume */}
        <SectionCard title="Resume">
          <CareerResumeUploadSection variant="profile" />
        </SectionCard>

        {/* Section 4: Account & Security */}
        <SectionCard title="Account & Security">
          <div className="divide-y divide-[#E9D5FF]/60">
            {CHANGE_PASSWORD_ENABLED ? (
              <>
                <SettingsRow
                  label="Change Password"
                  onClick={() => setShowPasswordForm((v) => !v)}
                />
                {showPasswordForm && (
                  <div className="space-y-3 py-3">
                    <input
                      type="password"
                      placeholder="Current password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      className="w-full rounded-lg border border-[#E9D5FF] px-3 py-2 text-sm"
                    />
                    <input
                      type="password"
                      placeholder="New password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full rounded-lg border border-[#E9D5FF] px-3 py-2 text-sm"
                    />
                    <input
                      type="password"
                      placeholder="Confirm new password"
                      value={confirmNewPassword}
                      onChange={(e) => setConfirmNewPassword(e.target.value)}
                      className="w-full rounded-lg border border-[#E9D5FF] px-3 py-2 text-sm"
                    />
                    <button
                      type="button"
                      onClick={() => void handleChangePassword()}
                      disabled={passwordStatus === 'saving'}
                      className="rounded-lg px-4 py-2 text-sm font-semibold text-white"
                      style={{ backgroundColor: MINGUS_PURPLE }}
                    >
                      {passwordStatus === 'saving' ? 'Saving…' : 'Save'}
                    </button>
                    {passwordStatus === 'error' && passwordError && (
                      <p className="text-sm text-red-600">{passwordError}</p>
                    )}
                  </div>
                )}
              </>
            ) : (
              <SettingsRow label="Change Password" comingSoon />
            )}
            <SettingsRow label="Notification Preferences" comingSoon />
            <SettingsRow label="Two-Factor Authentication" comingSoon />
          </div>
        </SectionCard>

        {/* Section 5: Subscription */}
        <SectionCard title="Subscription">
          <p className="mb-4 text-sm" style={{ color: SLATE_TEXT }}>
            Current plan:{' '}
            <span className="font-semibold">{tierLabel(tier)}</span>
          </p>
          <div className="flex flex-col gap-2">
            {tier === 'professional' ? (
              <button
                type="button"
                disabled
                className="cursor-not-allowed rounded-lg border border-[#E9D5FF] px-4 py-2.5 text-sm font-medium text-[#64748B] opacity-70"
              >
                Manage Billing — Coming soon
              </button>
            ) : (
              <button
                type="button"
                onClick={() => navigate('/settings/upgrade')}
                className="rounded-lg px-4 py-2.5 text-sm font-semibold text-white"
                style={{ backgroundColor: MINGUS_PURPLE }}
              >
                Upgrade
              </button>
            )}
            <SettingsRow label="View billing history" comingSoon />
          </div>
        </SectionCard>

        {/* Section 6: Support */}
        <SectionCard title="Support">
          <div className="divide-y divide-[#E9D5FF]/60">
            <SettingsRow
              label="Help & FAQ"
              href="https://support.mingusapp.com"
              external
            />
            <SettingsRow label="Contact Support" mailto="mailto:support@mingusapp.com" />
            <SettingsRow label="Send Feedback" comingSoon />
          </div>
        </SectionCard>

        {/* Sign Out */}
        <button
          type="button"
          onClick={() => void handleSignOut()}
          disabled={signingOut}
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl border-2 bg-transparent py-3 text-base font-semibold transition-opacity disabled:opacity-60"
          style={{ borderColor: MINGUS_PURPLE, color: MINGUS_PURPLE }}
        >
          {signingOut ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
              Signing out…
            </>
          ) : (
            'Sign Out'
          )}
        </button>
      </div>
    </div>
  );
};

export default YouTab;
