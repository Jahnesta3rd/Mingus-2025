import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Check,
  ChevronDown,
  ChevronUp,
  Loader2,
  Lock,
  Pencil,
  Upload,
  X,
} from 'lucide-react';
import { useAuth, type AuthUserTier } from '../hooks/useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';

type View = 'upload' | 'questions' | 'generating' | 'recommendation';

type ParseStatus = 'pending' | 'completed' | 'failed' | 'manual';

interface UploadedPlan {
  id: number;
  name: string;
  parse_status: ParseStatus;
  timedOut?: boolean;
}

interface PlanComparison {
  plan_name: string;
  plan_type?: string;
  estimated_annual_cost?: number;
  monthly_premium?: number;
  deductible?: number;
  oop_max?: number;
  score?: number;
}

interface RecommendationJson {
  summary?: string;
  recommended_plan_name?: string;
  key_reason?: string;
  when_to_reconsider?: string;
  plan_comparisons?: PlanComparison[];
  risk_assessment?: string;
  risk_flags?: string[];
  hsa_guidance?: string | null;
  disclaimer?: string;
}

interface UsageProfileResponse {
  usage?: {
    coverage_type?: string | null;
    primary_care_visits?: number | null;
    specialist_visits?: number | null;
    er_visits?: number | null;
    planned_procedure?: boolean | null;
    takes_rx?: boolean | null;
    rx_type?: string | null;
  };
  prefill_banner?: string | null;
}

interface RecommendationData {
  status?: 'not_generated';
  tier_locked?: boolean;
  upgrade_prompt?: string;
  recommendation?: RecommendationJson;
  recommended_plan_id?: number;
  recommended_plan_name?: string;
  expected_annual_cost_recommended?: number;
  expected_annual_cost_runner_up?: number;
  hsa_recommended?: boolean;
  hsa_annual_benefit?: number;
  risk_flags?: string[];
  benchmark_context?: {
    available?: boolean;
    comparison?: { summary_line?: string };
  };
  generated_at?: string;
  expires_at?: string;
}

interface ManualFormState {
  plan_name: string;
  plan_type: string;
  monthly_premium_employee: string;
  annual_deductible_individual: string;
  out_of_pocket_max_individual: string;
  has_hsa_eligible: boolean;
}

const GENERATING_MESSAGES = [
  'Reviewing your plan options...',
  'Running the numbers...',
  'Checking your usage patterns...',
  'Almost there...',
];

const EMPTY_MANUAL: ManualFormState = {
  plan_name: '',
  plan_type: 'PPO',
  monthly_premium_employee: '',
  annual_deductible_individual: '',
  out_of_pocket_max_individual: '',
  has_hsa_eligible: false,
};

function buildAuthHeaders(json = true): HeadersInit {
  const token = localStorage.getItem('mingus_token');
  const headers: Record<string, string> = { ...csrfHeaders() };
  if (json) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

function formatMoney(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '$0';
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function Chip({
  selected,
  onClick,
  children,
}: {
  selected: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3 py-1.5 text-sm transition-colors ${
        selected
          ? 'bg-[#7C3AED] text-white'
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
    >
      {children}
    </button>
  );
}

export default function HealthInsuranceAdvisor() {
  const { userTier } = useAuth();
  const tier: AuthUserTier = userTier ?? 'budget';
  const isProfessional = tier === 'professional';

  const [bootLoading, setBootLoading] = useState(true);
  const [currentView, setCurrentView] = useState<View>('upload');
  const [uploadedPlans, setUploadedPlans] = useState<UploadedPlan[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [prefillBanner, setPrefillBanner] = useState<string | null>(null);
  const [coverageType, setCoverageType] = useState('self');
  const [primaryCareVisits, setPrimaryCareVisits] = useState(3);
  const [specialistVisits, setSpecialistVisits] = useState(1);
  const [erVisits, setErVisits] = useState(0);
  const [plannedProcedure, setPlannedProcedure] = useState(false);
  const [takesRx, setTakesRx] = useState(false);
  const [rxType, setRxType] = useState('generic');
  const [submittingQuestions, setSubmittingQuestions] = useState(false);

  const [generatingMessageIndex, setGeneratingMessageIndex] = useState(0);
  const [generatingSlow, setGeneratingSlow] = useState(false);
  const [generatingError, setGeneratingError] = useState(false);

  const [recommendation, setRecommendation] = useState<RecommendationData | null>(null);
  const [recLoading, setRecLoading] = useState(false);
  const [comparisonOpen, setComparisonOpen] = useState(false);
  const [acceptDialogOpen, setAcceptDialogOpen] = useState(false);
  const [accepting, setAccepting] = useState(false);
  const [acceptSuccess, setAcceptSuccess] = useState(false);

  const [manualOpen, setManualOpen] = useState(false);
  const [manualForm, setManualForm] = useState<ManualFormState>(EMPTY_MANUAL);
  const [manualSaving, setManualSaving] = useState(false);
  const [manualTargetId, setManualTargetId] = useState<number | null>(null);

  const pollStartedRef = useRef<Record<number, number>>({});

  const readyPlanCount = useMemo(
    () =>
      uploadedPlans.filter((p) =>
        ['completed', 'manual'].includes(p.parse_status)
      ).length,
    [uploadedPlans]
  );

  const fetchPlans = useCallback(async () => {
    const res = await fetch('/api/benefits/insurance-plans', {
      credentials: 'include',
      headers: buildAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to load plans');
    const data = (await res.json()) as Array<{
      plan_id: number;
      plan_name: string;
      parse_status: ParseStatus;
    }>;
    setUploadedPlans(
      data.map((p) => ({
        id: p.plan_id,
        name: p.plan_name,
        parse_status: p.parse_status,
      }))
    );
  }, []);

  const fetchRecommendation = useCallback(async (): Promise<RecommendationData> => {
    const res = await fetch('/api/benefits/insurance-recommendation', {
      credentials: 'include',
      headers: buildAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to load recommendation');
    return (await res.json()) as RecommendationData;
  }, []);

  const loadUsageProfile = useCallback(async () => {
    const res = await fetch('/api/benefits/insurance-plans/usage-profile', {
      credentials: 'include',
      headers: buildAuthHeaders(),
    });
    if (!res.ok) return;
    const data = (await res.json()) as UsageProfileResponse;
    if (data.prefill_banner) setPrefillBanner(data.prefill_banner);
    const u = data.usage;
    if (!u) return;
    if (u.coverage_type) setCoverageType(u.coverage_type);
    if (u.primary_care_visits != null) setPrimaryCareVisits(u.primary_care_visits);
    if (u.specialist_visits != null) setSpecialistVisits(u.specialist_visits);
    if (u.er_visits != null) setErVisits(u.er_visits);
    if (u.planned_procedure != null) setPlannedProcedure(u.planned_procedure);
    if (u.takes_rx != null) setTakesRx(u.takes_rx);
    if (u.rx_type) setRxType(u.rx_type);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const rec = await fetchRecommendation();
        if (cancelled) return;
        if (rec.status !== 'not_generated') {
          setRecommendation(rec);
          setCurrentView('recommendation');
        } else {
          await fetchPlans();
        }
      } catch {
        if (!cancelled) setError('Unable to load. Try again.');
      } finally {
        if (!cancelled) setBootLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [fetchRecommendation, fetchPlans]);

  useEffect(() => {
    if (currentView === 'questions') {
      void loadUsageProfile();
    }
  }, [currentView, loadUsageProfile]);

  const pollPlanStatus = useCallback((planId: number) => {
    if (pollStartedRef.current[planId]) return;
    pollStartedRef.current[planId] = Date.now();

    const interval = window.setInterval(async () => {
      const elapsed = Date.now() - pollStartedRef.current[planId];
      if (elapsed > 30_000) {
        window.clearInterval(interval);
        setUploadedPlans((prev) =>
          prev.map((p) =>
            p.id === planId && p.parse_status === 'pending'
              ? { ...p, timedOut: true, parse_status: 'failed' }
              : p
          )
        );
        return;
      }

      try {
        const res = await fetch(
          `/api/benefits/insurance-plans/${planId}/status`,
          { credentials: 'include', headers: buildAuthHeaders() }
        );
        if (!res.ok) return;
        const data = (await res.json()) as { parse_status: ParseStatus };
        if (data.parse_status !== 'pending') {
          window.clearInterval(interval);
          setUploadedPlans((prev) =>
            prev.map((p) =>
              p.id === planId ? { ...p, parse_status: data.parse_status } : p
            )
          );
        }
      } catch {
        /* keep polling */
      }
    }, 3000);
  }, []);

  const handleFiles = useCallback(
    async (files: FileList | File[]) => {
      const list = Array.from(files);
      if (list.length === 0) return;
      setUploading(true);
      setError(null);

      for (const file of list) {
        const ext = file.name.toLowerCase();
        if (!ext.endsWith('.pdf') && !ext.endsWith('.docx')) {
          setError('Only .pdf and .docx files are allowed.');
          continue;
        }

        const formData = new FormData();
        formData.append('files', file);

        try {
          const res = await fetch('/api/benefits/insurance-plans/upload', {
            method: 'POST',
            credentials: 'include',
            headers: buildAuthHeaders(false),
            body: formData,
          });
          if (!res.ok) throw new Error('Upload failed');
          const data = (await res.json()) as
            | { plan_id: number; filename: string; parse_status: ParseStatus }
            | Array<{ plan_id: number; filename: string; parse_status: ParseStatus }>;
          const items = Array.isArray(data) ? data : [data];
          for (const item of items) {
            setUploadedPlans((prev) => [
              ...prev,
              {
                id: item.plan_id,
                name: item.filename,
                parse_status: item.parse_status,
              },
            ]);
            if (item.parse_status === 'pending') {
              pollPlanStatus(item.plan_id);
            }
          }
        } catch {
          setError('Upload failed. Please try again.');
        }
      }
      setUploading(false);
    },
    [pollPlanStatus]
  );

  const openManualModal = (plan?: UploadedPlan) => {
    setManualTargetId(plan?.id ?? null);
    setManualForm({
      ...EMPTY_MANUAL,
      plan_name: plan?.name.replace(/\.(pdf|docx)$/i, '') ?? '',
    });
    setManualOpen(true);
  };

  const submitManualPlan = async () => {
    if (!manualForm.plan_name.trim()) return;
    setManualSaving(true);
    try {
      const body = {
        plan_name: manualForm.plan_name.trim(),
        plan_type: manualForm.plan_type,
        monthly_premium_employee: Number(manualForm.monthly_premium_employee) || 0,
        annual_deductible_individual:
          Number(manualForm.annual_deductible_individual) || 0,
        out_of_pocket_max_individual:
          Number(manualForm.out_of_pocket_max_individual) || 0,
        has_hsa_eligible: manualForm.has_hsa_eligible,
      };
      const res = await fetch('/api/benefits/insurance-plans/manual-create', {
        method: 'POST',
        credentials: 'include',
        headers: buildAuthHeaders(),
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('manual create failed');
      const data = (await res.json()) as {
        plan_id: number;
        plan_name: string;
        parse_status: ParseStatus;
      };

      if (manualTargetId != null) {
        setUploadedPlans((prev) =>
          prev.filter((p) => p.id !== manualTargetId).concat({
            id: data.plan_id,
            name: data.plan_name,
            parse_status: 'manual',
          })
        );
      } else {
        setUploadedPlans((prev) => [
          ...prev,
          { id: data.plan_id, name: data.plan_name, parse_status: 'manual' },
        ]);
      }
      setManualOpen(false);
      setManualForm(EMPTY_MANUAL);
    } catch {
      setError('Unable to save plan. Try again.');
    } finally {
      setManualSaving(false);
    }
  };

  const submitQuestions = async () => {
    setSubmittingQuestions(true);
    setError(null);
    try {
      const usageBody = {
        coverage_type: coverageType,
        primary_care_visits: primaryCareVisits,
        specialist_visits: specialistVisits,
        er_visits: erVisits,
        planned_procedure: plannedProcedure,
        takes_rx: takesRx,
        rx_type: takesRx ? rxType : null,
      };
      const saveRes = await fetch('/api/benefits/insurance-plans/usage-profile', {
        method: 'POST',
        credentials: 'include',
        headers: buildAuthHeaders(),
        body: JSON.stringify(usageBody),
      });
      if (!saveRes.ok) throw new Error('usage save failed');

      setCurrentView('generating');
      setGeneratingError(false);
      setGeneratingSlow(false);

      const genRes = await fetch('/api/benefits/insurance-recommendation/generate', {
        method: 'POST',
        credentials: 'include',
        headers: buildAuthHeaders(),
        body: '{}',
      });
      if (!genRes.ok) {
        const errBody = (await genRes.json()) as { error?: string };
        throw new Error(errBody.error || 'Generation failed');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to generate recommendation.');
      setCurrentView('questions');
    } finally {
      setSubmittingQuestions(false);
    }
  };

  useEffect(() => {
    if (currentView !== 'generating') return;

    const msgTimer = window.setInterval(() => {
      setGeneratingMessageIndex((i) => (i + 1) % GENERATING_MESSAGES.length);
    }, 2000);

    const slowTimer = window.setTimeout(() => setGeneratingSlow(true), 20_000);

    const poll = window.setInterval(async () => {
      try {
        const rec = await fetchRecommendation();
        if (rec.status !== 'not_generated') {
          setRecommendation(rec);
          setCurrentView('recommendation');
        }
      } catch {
        setGeneratingError(true);
      }
    }, 2000);

    return () => {
      window.clearInterval(msgTimer);
      window.clearTimeout(slowTimer);
      window.clearInterval(poll);
    };
  }, [currentView, fetchRecommendation]);

  useEffect(() => {
    if (currentView !== 'recommendation') return;
    let cancelled = false;
    (async () => {
      setRecLoading(true);
      try {
        const rec = await fetchRecommendation();
        if (!cancelled) setRecommendation(rec);
      } catch {
        if (!cancelled) setError('Unable to load. Try again.');
      } finally {
        if (!cancelled) setRecLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [currentView, fetchRecommendation]);

  const recommendedMonthlyPremium = useMemo(() => {
    const recJson = recommendation?.recommendation;
    const name = recommendation?.recommended_plan_name;
    const match = recJson?.plan_comparisons?.find((p) => p.plan_name === name);
    return match?.monthly_premium ?? null;
  }, [recommendation]);

  const acceptPlan = async () => {
    if (!recommendation?.recommended_plan_id) return;
    setAccepting(true);
    try {
      const res = await fetch('/api/benefits/insurance-plans/accept', {
        method: 'POST',
        credentials: 'include',
        headers: buildAuthHeaders(),
        body: JSON.stringify({ plan_id: recommendation.recommended_plan_id }),
      });
      if (!res.ok) throw new Error('accept failed');
      setAcceptSuccess(true);
      setAcceptDialogOpen(false);
    } catch {
      setError('Unable to accept plan. Try again.');
    } finally {
      setAccepting(false);
    }
  };

  const renderStatusIcon = (plan: UploadedPlan) => {
    if (plan.parse_status === 'pending') {
      return <Loader2 className="h-4 w-4 animate-spin text-teal-600" aria-hidden />;
    }
    if (plan.parse_status === 'completed') {
      return <Check className="h-4 w-4 text-green-600" aria-hidden />;
    }
    if (plan.parse_status === 'manual') {
      return <Pencil className="h-4 w-4 text-gray-400" aria-hidden />;
    }
    return <X className="h-4 w-4 text-red-500" aria-hidden />;
  };

  const renderUploadView = () => (
    <div className="rounded-xl bg-white p-6 shadow-sm">
      <h1 className="text-xl font-semibold text-gray-800">Health Insurance Advisor</h1>
      <p className="mt-1 text-sm text-gray-500">
        Upload your plan options and we&apos;ll find the best fit for your usage and budget.
      </p>

      <label
        className="mt-6 block cursor-pointer rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 p-8 text-center"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          void handleFiles(e.dataTransfer.files);
        }}
      >
        <Upload className="mx-auto h-8 w-8 text-gray-400" aria-hidden />
        <p className="mt-2 text-sm text-gray-600">
          Drag and drop PDF or DOCX files here, or click to browse
        </p>
        <input
          type="file"
          accept=".pdf,.docx"
          multiple
          className="hidden"
          onChange={(e) => {
            if (e.target.files) void handleFiles(e.target.files);
          }}
        />
      </label>

      {uploading ? (
        <p className="mt-3 text-sm text-gray-500">Uploading…</p>
      ) : null}

      {uploadedPlans.length > 0 ? (
        <ul className="mt-4 space-y-2">
          {uploadedPlans.map((plan) => (
            <li
              key={plan.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-gray-50 px-3 py-2 text-sm"
            >
              <span className="font-medium text-gray-700">{plan.name}</span>
              <div className="flex items-center gap-2">
                {renderStatusIcon(plan)}
                {plan.parse_status === 'failed' || plan.timedOut ? (
                  <button
                    type="button"
                    onClick={() => openManualModal(plan)}
                    className="text-xs text-teal-600 underline"
                  >
                    Failed to parse — enter manually
                  </button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      <button
        type="button"
        onClick={() => openManualModal()}
        className="mt-3 text-sm text-[#7C3AED] underline"
      >
        Enter a plan manually
      </button>

      <button
        type="button"
        disabled={readyPlanCount < 2}
        onClick={() => setCurrentView('questions')}
        className="mt-6 w-full rounded-xl bg-teal-600 px-4 py-3 text-sm font-semibold text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Continue →
      </button>
      {readyPlanCount < 2 ? (
        <p className="mt-2 text-center text-xs text-gray-400">
          Upload or enter at least 2 plans to continue
        </p>
      ) : null}
    </div>
  );

  const renderQuestionsView = () => (
    <div className="rounded-xl bg-white p-6 shadow-sm">
      {prefillBanner ? (
        <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          {prefillBanner}
        </div>
      ) : null}

      <h2 className="text-xl font-semibold text-gray-800">
        Help us personalize your recommendation
      </h2>
      <p className="mt-1 text-sm text-gray-500">Takes 60 seconds.</p>

      <div className="mt-6 space-y-6">
        <div>
          <p className="text-sm font-medium text-gray-700">Who are you covering?</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Chip selected={coverageType === 'self'} onClick={() => setCoverageType('self')}>
              Just me
            </Chip>
            <Chip selected={coverageType === 'spouse'} onClick={() => setCoverageType('spouse')}>
              Me + spouse
            </Chip>
            <Chip selected={coverageType === 'kids'} onClick={() => setCoverageType('kids')}>
              Me + kids
            </Chip>
            <Chip selected={coverageType === 'family'} onClick={() => setCoverageType('family')}>
              Whole family
            </Chip>
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-gray-700">
            How many doctor visits last year?
          </p>
          <input
            type="range"
            min={0}
            max={10}
            step={1}
            value={primaryCareVisits}
            onChange={(e) => setPrimaryCareVisits(Number(e.target.value))}
            className="mt-2 w-full accent-[#7C3AED]"
          />
          <p className="text-sm text-gray-500">{primaryCareVisits} visits</p>
        </div>

        <div>
          <p className="text-sm font-medium text-gray-700">Specialist visits?</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Chip selected={specialistVisits === 0} onClick={() => setSpecialistVisits(0)}>
              None
            </Chip>
            <Chip selected={specialistVisits === 1} onClick={() => setSpecialistVisits(1)}>
              1-2
            </Chip>
            <Chip selected={specialistVisits === 3} onClick={() => setSpecialistVisits(3)}>
              3-5
            </Chip>
            <Chip selected={specialistVisits === 5} onClick={() => setSpecialistVisits(5)}>
              5+
            </Chip>
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-gray-700">ER or urgent care visits?</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Chip selected={erVisits === 0} onClick={() => setErVisits(0)}>
              None
            </Chip>
            <Chip selected={erVisits === 1} onClick={() => setErVisits(1)}>
              Once
            </Chip>
            <Chip selected={erVisits === 2} onClick={() => setErVisits(2)}>
              More than once
            </Chip>
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-gray-700">
            Planned procedure or surgery in the next 12 months?
          </p>
          <div className="mt-2 flex gap-2">
            <Chip selected={plannedProcedure} onClick={() => setPlannedProcedure(true)}>
              Yes
            </Chip>
            <Chip selected={!plannedProcedure} onClick={() => setPlannedProcedure(false)}>
              No
            </Chip>
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-gray-700">
            Do you take regular prescription medications?
          </p>
          <div className="mt-2 flex gap-2">
            <Chip selected={takesRx} onClick={() => setTakesRx(true)}>
              Yes
            </Chip>
            <Chip selected={!takesRx} onClick={() => setTakesRx(false)}>
              No
            </Chip>
          </div>
          {takesRx ? (
            <div className="mt-3">
              <p className="text-sm text-gray-600">Generic, brand-name, or specialty?</p>
              <div className="mt-2 flex flex-wrap gap-2">
                <Chip selected={rxType === 'generic'} onClick={() => setRxType('generic')}>
                  Generic
                </Chip>
                <Chip selected={rxType === 'brand'} onClick={() => setRxType('brand')}>
                  Brand-name
                </Chip>
                <Chip selected={rxType === 'specialty'} onClick={() => setRxType('specialty')}>
                  Specialty
                </Chip>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <button
        type="button"
        disabled={submittingQuestions}
        onClick={() => void submitQuestions()}
        className="mt-8 w-full rounded-xl bg-[#7C3AED] px-4 py-3 text-sm font-semibold text-white hover:bg-[#6D28D9] disabled:opacity-60"
      >
        {submittingQuestions ? 'Saving…' : 'Get my recommendation →'}
      </button>
    </div>
  );

  const renderGeneratingView = () => (
    <div className="rounded-xl bg-white p-6 shadow-sm">
      <div className="flex flex-col items-center py-12 text-center">
        <div
          className="h-10 w-10 animate-spin rounded-full border-2 border-[#7C3AED] border-t-transparent"
          role="status"
          aria-label="Generating recommendation"
        />
        <p className="mt-4 text-sm text-gray-600">
          {GENERATING_MESSAGES[generatingMessageIndex]}
        </p>
        {generatingSlow ? (
          <p className="mt-2 text-xs text-gray-400">
            Still working — this can take a moment.
          </p>
        ) : null}
        {generatingError ? (
          <button
            type="button"
            onClick={() => {
              setGeneratingError(false);
              void submitQuestions();
            }}
            className="mt-4 text-sm text-teal-600 underline"
          >
            Try again
          </button>
        ) : null}
      </div>
    </div>
  );

  const renderBudgetRecommendation = (rec: RecommendationData) => {
    const comparisons = rec.recommendation?.plan_comparisons ?? [];
    return (
      <div className="rounded-xl bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-gray-800">Your Plan Comparison</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead>
              <tr className="border-b text-gray-500">
                <th className="py-2 pr-4">Plan</th>
                <th className="py-2 pr-4">Est. annual cost</th>
                <th className="py-2 pr-4">Deductible</th>
                <th className="py-2">OOP max</th>
              </tr>
            </thead>
            <tbody>
              {comparisons.map((row) => (
                <tr key={row.plan_name} className="border-b border-gray-100">
                  <td className="py-2 pr-4 font-medium text-gray-800">{row.plan_name}</td>
                  <td className="py-2 pr-4">{formatMoney(row.estimated_annual_cost)}</td>
                  <td className="py-2 pr-4">{formatMoney(row.deductible)}</td>
                  <td className="py-2">{formatMoney(row.oop_max)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="relative mt-6">
          <div className="pointer-events-none rounded-xl border border-gray-200 p-6 blur-sm opacity-50">
            <div className="h-24 rounded-lg bg-gray-100" />
          </div>
          <div className="absolute inset-0 flex flex-col items-center justify-center px-4 text-center">
            <Lock className="h-6 w-6 text-[#7C3AED]" aria-hidden />
            <p className="mt-2 font-medium text-gray-800">
              See your personalized recommendation
            </p>
            <p className="mt-1 max-w-md text-sm text-gray-500">
              {rec.upgrade_prompt ??
                'Upgrade to Mid-tier to unlock risk analysis, HSA guidance, and a plan recommendation based on your health usage.'}
            </p>
            <Link
              to="/dashboard/upgrade"
              className="mt-4 rounded-full bg-[#7C3AED] px-5 py-2 text-sm font-medium text-white hover:bg-[#6D28D9]"
            >
              View Plans →
            </Link>
          </div>
        </div>
      </div>
    );
  };

  const renderFullRecommendation = (rec: RecommendationData) => {
    const recJson = rec.recommendation ?? {};
    const recCost = rec.expected_annual_cost_recommended ?? 0;
    const runnerCost = rec.expected_annual_cost_runner_up ?? 0;
    const maxCost = Math.max(recCost, runnerCost, 1);
    const riskItems =
      recJson.risk_flags ??
      (rec.risk_flags?.length ? rec.risk_flags : recJson.risk_assessment ? [recJson.risk_assessment] : []);
    const comparisons = recJson.plan_comparisons ?? [];
    const recommendedName = rec.recommended_plan_name ?? recJson.recommended_plan_name ?? '';

    return (
      <div className="rounded-xl bg-white p-6 shadow-sm">
        {acceptSuccess ? (
          <div className="mb-4 rounded-xl border border-green-200 bg-green-50 p-3 text-sm text-green-800">
            Added to your monthly budget. ✓
          </div>
        ) : null}

        <div className="rounded-xl border-l-4 border-[#7C3AED] bg-white p-5 shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wide text-[#7C3AED]">
            Recommended
          </span>
          <h2 className="mt-1 text-xl font-bold text-gray-800">{recommendedName}</h2>
          {recJson.key_reason ? (
            <p className="mt-1 text-sm italic text-gray-500">{recJson.key_reason}</p>
          ) : null}

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div>
              <p className="text-xs text-gray-500">Recommended</p>
              <div className="mt-1 h-3 overflow-hidden rounded-full bg-gray-100">
                <div
                  className="h-full rounded-full bg-teal-500"
                  style={{ width: `${(recCost / maxCost) * 100}%` }}
                />
              </div>
              <p className="mt-1 text-sm font-medium text-gray-800">
                {formatMoney(recCost)}/year
              </p>
            </div>
            {runnerCost > 0 ? (
              <div>
                <p className="text-xs text-gray-500">Runner-up</p>
                <div className="mt-1 h-3 overflow-hidden rounded-full bg-gray-100">
                  <div
                    className="h-full rounded-full bg-gray-400"
                    style={{ width: `${(runnerCost / maxCost) * 100}%` }}
                  />
                </div>
                <p className="mt-1 text-sm font-medium text-gray-800">
                  {formatMoney(runnerCost)}/year
                </p>
              </div>
            ) : null}
          </div>
        </div>

        {riskItems.length > 0 ? (
          <div className="mt-3 space-y-2">
            {riskItems.map((flag) => (
              <div
                key={flag.slice(0, 40)}
                className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800"
              >
                ⚠ {flag}
              </div>
            ))}
          </div>
        ) : null}

        {rec.hsa_recommended && recJson.hsa_guidance ? (
          <div className="mt-3 rounded-xl border border-green-200 bg-green-50 p-3 text-sm text-green-800">
            <p className="font-medium">💰 HSA Opportunity</p>
            <p className="mt-1">{recJson.hsa_guidance}</p>
          </div>
        ) : null}

        {rec.benchmark_context?.available && rec.benchmark_context.comparison?.summary_line ? (
          <div className="mt-3 rounded-xl border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
            📊 {rec.benchmark_context.comparison.summary_line}
          </div>
        ) : null}

        <div className="mt-4">
          <button
            type="button"
            onClick={() => setComparisonOpen((o) => !o)}
            className="flex items-center gap-1 text-sm font-medium text-gray-700"
          >
            See all {comparisons.length} plans compared
            {comparisonOpen ? (
              <ChevronUp className="h-4 w-4" aria-hidden />
            ) : (
              <ChevronDown className="h-4 w-4" aria-hidden />
            )}
          </button>
          {comparisonOpen ? (
            <div className="mt-2 overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-gray-500">
                    <th className="py-2 pr-3">Plan</th>
                    <th className="py-2 pr-3">Type</th>
                    <th className="py-2 pr-3">Est. Annual</th>
                    <th className="py-2 pr-3">Deductible</th>
                    <th className="py-2 pr-3">OOP Max</th>
                    <th className="py-2">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisons.map((row) => {
                    const isRec = row.plan_name === recommendedName;
                    return (
                      <tr
                        key={row.plan_name}
                        className={`border-b border-gray-100 ${
                          isRec ? 'bg-purple-50 font-medium' : ''
                        }`}
                      >
                        <td className="py-2 pr-3">{row.plan_name}</td>
                        <td className="py-2 pr-3">{row.plan_type ?? '—'}</td>
                        <td className="py-2 pr-3">
                          {formatMoney(row.estimated_annual_cost)}
                        </td>
                        <td className="py-2 pr-3">{formatMoney(row.deductible)}</td>
                        <td className="py-2 pr-3">{formatMoney(row.oop_max)}</td>
                        <td className="py-2">{row.score ?? '—'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>

        {recJson.when_to_reconsider ? (
          <p className="mt-4 text-xs text-gray-400">{recJson.when_to_reconsider}</p>
        ) : null}

        {isProfessional ? (
          <button
            type="button"
            onClick={() => setAcceptDialogOpen(true)}
            className="mt-6 rounded-full border border-[#7C3AED] px-6 py-2 text-sm font-medium text-[#7C3AED] hover:bg-purple-50"
          >
            Accept this plan
          </button>
        ) : null}

        {recJson.disclaimer ? (
          <p className="mt-6 text-center text-xs text-gray-400">{recJson.disclaimer}</p>
        ) : null}
      </div>
    );
  };

  const renderRecommendationView = () => {
    if (recLoading || !recommendation) {
      return (
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <div className="h-32 animate-pulse rounded-lg bg-gray-100" />
        </div>
      );
    }
    if (recommendation.tier_locked) {
      return renderBudgetRecommendation(recommendation);
    }
    return renderFullRecommendation(recommendation);
  };

  if (bootLoading) {
    return (
      <div className="mx-auto max-w-2xl p-4">
        <div className="h-48 animate-pulse rounded-xl bg-gray-100" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4 p-4">
      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
          <button
            type="button"
            onClick={() => {
              setError(null);
              window.location.reload();
            }}
            className="ml-2 underline"
          >
            Try again
          </button>
        </div>
      ) : null}

      {currentView === 'upload' ? renderUploadView() : null}
      {currentView === 'questions' ? renderQuestionsView() : null}
      {currentView === 'generating' ? renderGeneratingView() : null}
      {currentView === 'recommendation' ? renderRecommendationView() : null}

      {manualOpen ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 sm:items-center">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-white p-6 shadow-lg sm:rounded-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-800">Enter plan manually</h3>
              <button type="button" onClick={() => setManualOpen(false)} aria-label="Close">
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>
            <div className="space-y-3">
              <label className="block text-sm">
                <span className="text-gray-700">Plan name *</span>
                <input
                  type="text"
                  value={manualForm.plan_name}
                  onChange={(e) =>
                    setManualForm((f) => ({ ...f, plan_name: e.target.value }))
                  }
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2"
                />
              </label>
              <label className="block text-sm">
                <span className="text-gray-700">Plan type</span>
                <select
                  value={manualForm.plan_type}
                  onChange={(e) =>
                    setManualForm((f) => ({ ...f, plan_type: e.target.value }))
                  }
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2"
                >
                  {['HMO', 'PPO', 'HDHP', 'EPO', 'POS'].map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm">
                <span className="text-gray-700">Monthly premium (employee)</span>
                <input
                  type="number"
                  min={0}
                  value={manualForm.monthly_premium_employee}
                  onChange={(e) =>
                    setManualForm((f) => ({
                      ...f,
                      monthly_premium_employee: e.target.value,
                    }))
                  }
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2"
                />
              </label>
              <label className="block text-sm">
                <span className="text-gray-700">Annual deductible (individual)</span>
                <input
                  type="number"
                  min={0}
                  value={manualForm.annual_deductible_individual}
                  onChange={(e) =>
                    setManualForm((f) => ({
                      ...f,
                      annual_deductible_individual: e.target.value,
                    }))
                  }
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2"
                />
              </label>
              <label className="block text-sm">
                <span className="text-gray-700">Out-of-pocket max (individual)</span>
                <input
                  type="number"
                  min={0}
                  value={manualForm.out_of_pocket_max_individual}
                  onChange={(e) =>
                    setManualForm((f) => ({
                      ...f,
                      out_of_pocket_max_individual: e.target.value,
                    }))
                  }
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2"
                />
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={manualForm.has_hsa_eligible}
                  onChange={(e) =>
                    setManualForm((f) => ({ ...f, has_hsa_eligible: e.target.checked }))
                  }
                />
                HSA-eligible plan
              </label>
            </div>
            <button
              type="button"
              disabled={manualSaving || !manualForm.plan_name.trim()}
              onClick={() => void submitManualPlan()}
              className="mt-6 w-full rounded-xl bg-teal-600 px-4 py-3 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-60"
            >
              {manualSaving ? 'Saving…' : 'Save plan'}
            </button>
          </div>
        </div>
      ) : null}

      {acceptDialogOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-lg">
            <p className="text-sm text-gray-700">
              Add {formatMoney(recommendedMonthlyPremium)}/month premium to your budget?
            </p>
            <div className="mt-4 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setAcceptDialogOpen(false)}
                className="rounded-lg px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={accepting}
                onClick={() => void acceptPlan()}
                className="rounded-lg bg-[#7C3AED] px-4 py-2 text-sm font-medium text-white hover:bg-[#6D28D9] disabled:opacity-60"
              >
                {accepting ? 'Confirming…' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export { HealthInsuranceAdvisor };
