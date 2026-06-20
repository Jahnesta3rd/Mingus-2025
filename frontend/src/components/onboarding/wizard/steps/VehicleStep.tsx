import React, { useCallback, useRef, useState } from 'react';
import { useAuth } from '../../../../hooks/useAuth';
import { csrfHeaders } from '../../../../utils/csrfHeaders';
import type { StepProps } from '../StepDefinitions';

type OilBucket = 'recent' | '3-6mo' | '6-12mo' | 'over_year' | 'unknown';
type MajorServiceStatus = 'up_to_date' | 'overdue' | 'scheduled' | 'unknown';
type Field =
  | 'vin'
  | 'make'
  | 'model'
  | 'year'
  | 'currentMileage'
  | 'monthlyMiles'
  | 'garageZip'
  | 'monthly_payment'
  | 'insurance_monthly'
  | 'last_oil_change_bucket'
  | 'major_service_status'
  | 'known_issues';
type FieldErrors = Partial<Record<Field, string>>;

const POPULAR_MAKES = [
  'Honda',
  'Toyota',
  'Nissan',
  'Ford',
  'Chevrolet',
  'BMW',
  'Mercedes-Benz',
  'Audi',
  'Lexus',
  'Acura',
  'Infiniti',
  'Hyundai',
  'Kia',
  'Mazda',
  'Subaru',
  'Tesla',
  'GMC',
  'Jeep',
  'Ram',
  'Volkswagen',
  'Volvo',
  'Cadillac',
  'Buick',
] as const;

const POPULAR_MODELS: Record<string, string[]> = {
  Honda: ['Civic', 'Accord', 'CR-V', 'Pilot', 'HR-V', 'Passport'],
  Toyota: ['Camry', 'Corolla', 'RAV4', 'Highlander', 'Prius', '4Runner'],
  Nissan: ['Altima', 'Sentra', 'Rogue', 'Murano', 'Pathfinder', 'Maxima'],
  Ford: ['F-150', 'Explorer', 'Escape', 'Mustang', 'Edge', 'Expedition'],
  Chevrolet: ['Silverado', 'Equinox', 'Malibu', 'Tahoe', 'Suburban', 'Camaro'],
  BMW: ['3 Series', '5 Series', 'X3', 'X5', 'X1', '7 Series'],
  'Mercedes-Benz': ['C-Class', 'E-Class', 'GLC', 'GLE', 'A-Class', 'S-Class'],
  Audi: ['A4', 'A6', 'Q5', 'Q7', 'A3', 'Q3'],
  Lexus: ['ES', 'RX', 'IS', 'NX', 'GX', 'LS'],
  Acura: ['TLX', 'RDX', 'MDX', 'ILX', 'NSX', 'RLX'],
  Infiniti: ['Q50', 'QX60', 'QX80', 'Q60', 'QX50', 'G37'],
  Hyundai: ['Elantra', 'Sonata', 'Tucson', 'Santa Fe', 'Palisade', 'Veloster'],
  Kia: ['Optima', 'Sorento', 'Sportage', 'Telluride', 'Forte', 'Stinger'],
  Mazda: ['CX-5', 'Mazda3', 'CX-9', 'Mazda6', 'CX-3', 'MX-5 Miata'],
  Subaru: ['Outback', 'Forester', 'Impreza', 'Legacy', 'Ascent', 'WRX'],
  Tesla: ['Model 3', 'Model Y', 'Model S', 'Model X', 'Cybertruck'],
  GMC: ['Sierra', 'Yukon', 'Acadia', 'Terrain', 'Canyon'],
  Jeep: ['Wrangler', 'Grand Cherokee', 'Cherokee', 'Compass', 'Renegade', 'Gladiator'],
  Ram: ['1500', '2500', '3500', 'ProMaster'],
  Volkswagen: ['Jetta', 'Passat', 'Tiguan', 'Atlas', 'GTI', 'ID.4'],
  Volvo: ['XC60', 'XC90', 'S60', 'V60', 'XC40'],
  Cadillac: ['Escalade', 'XT5', 'CT5', 'XT6', 'XT4'],
  Buick: ['Enclave', 'Encore', 'Envision', 'Regal'],
};

const YEARS = Array.from({ length: 30 }, (_, i) => new Date().getFullYear() - i);

const VIN_REGEX = /^[A-HJ-NPR-Z0-9]{17}$/;

const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 text-[#1E293B] placeholder:text-[#64748B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';
const labelClass = 'mb-1.5 block text-sm font-medium text-[#1E293B]';
const helperClass = 'mt-1 text-xs text-[#64748B]';

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

function firstOfNextMonthIso(): string {
  const now = new Date();
  const next = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  next.setHours(12, 0, 0, 0);
  return next.toISOString().slice(0, 10);
}

function readVehicle0(initialData: Record<string, unknown>): Record<string, unknown> | null {
  const vehicles = initialData.vehicles;
  if (Array.isArray(vehicles) && vehicles[0] && typeof vehicles[0] === 'object') {
    return vehicles[0] as Record<string, unknown>;
  }
  return null;
}

export default function VehicleStep({ initialData, onSubmit, onSkip, isSubmitting: isSkipInFlight }: StepProps) {
  const { getAccessToken } = useAuth();
  const currentYear = new Date().getFullYear();
  const v0 = readVehicle0(initialData);

  const [hasVehicle, setHasVehicle] = useState<boolean>(
    typeof initialData.has_vehicle === 'boolean' ? initialData.has_vehicle : true
  );
  const [vin, setVin] = useState<string>(
    typeof v0?.vin === 'string' ? v0.vin : typeof initialData.vin === 'string' ? initialData.vin : ''
  );
  const [make, setMake] = useState<string>(
    typeof v0?.make === 'string' ? v0.make : typeof initialData.make === 'string' ? initialData.make : ''
  );
  const [model, setModel] = useState<string>(
    typeof v0?.model === 'string' ? v0.model : typeof initialData.model === 'string' ? initialData.model : ''
  );
  const [year, setYear] = useState<string>(() => {
    const y = v0?.year ?? initialData.year;
    if (typeof y === 'number') return String(y);
    if (typeof y === 'string') return y;
    return '';
  });
  const [trim, setTrim] = useState<string>(typeof v0?.trim === 'string' ? v0.trim : '');
  const [currentMileage, setCurrentMileage] = useState<string>(() => {
    const m = v0?.current_mileage ?? initialData.mileage ?? initialData.current_mileage;
    if (typeof m === 'number') return String(m);
    if (typeof m === 'string') return m;
    return '';
  });
  const [monthlyMiles, setMonthlyMiles] = useState<string>(() => {
    const m = v0?.monthly_miles;
    if (typeof m === 'number') return String(m);
    if (typeof m === 'string') return m;
    return '';
  });
  const [garageZip, setGarageZip] = useState<string>(
    typeof v0?.user_zipcode === 'string'
      ? v0.user_zipcode
      : typeof initialData.garage_zip === 'string'
        ? initialData.garage_zip
        : ''
  );
  const [assignedMsa, setAssignedMsa] = useState<string>(
    typeof v0?.assigned_msa === 'string' ? v0.assigned_msa : ''
  );
  const [vinLookupLoading, setVinLookupLoading] = useState(false);
  const [vinValidationError, setVinValidationError] = useState<string | null>(null);
  const [zipLookupLoading, setZipLookupLoading] = useState(false);
  const [zipValidationError, setZipValidationError] = useState<string | null>(null);
  const [vinResolved, setVinResolved] = useState(false);

  const [monthlyPayment, setMonthlyPayment] = useState<string>(
    typeof initialData.monthly_payment === 'number'
      ? String(initialData.monthly_payment)
      : typeof initialData.monthly_payment === 'string'
        ? initialData.monthly_payment
        : typeof v0?.monthly_payment === 'number'
          ? String(v0.monthly_payment)
          : ''
  );
  const [monthlyFuel, setMonthlyFuel] = useState<string>(() => {
    const v = initialData.monthly_fuel;
    if (typeof v === 'number' && v > 0) return String(v);
    if (typeof v === 'string' && v.trim()) return v;
    if (v0 && typeof v0.monthly_fuel === 'number' && v0.monthly_fuel > 0) return String(v0.monthly_fuel);
    return '';
  });
  const [insuranceMonthly, setInsuranceMonthly] = useState<string>(
    typeof initialData.insurance_monthly === 'number'
      ? String(initialData.insurance_monthly)
      : typeof initialData.insurance_monthly === 'string'
        ? initialData.insurance_monthly
        : ''
  );
  const [lastOilChangeBucket, setLastOilChangeBucket] = useState<OilBucket>(
    typeof initialData.last_oil_change_bucket === 'string'
      ? (initialData.last_oil_change_bucket as OilBucket)
      : 'unknown'
  );
  const [majorServiceStatus, setMajorServiceStatus] = useState<MajorServiceStatus>(
    typeof initialData.major_service_status === 'string'
      ? (initialData.major_service_status as MajorServiceStatus)
      : 'unknown'
  );
  const [knownIssues, setKnownIssues] = useState<string>(
    typeof initialData.known_issues === 'string' ? initialData.known_issues : ''
  );
  const [errors, setErrors] = useState<FieldErrors>({});
  const [showValidationSummary, setShowValidationSummary] = useState(false);
  const [submitBanner, setSubmitBanner] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const vinDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const zipDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const makeOptions = make && !(POPULAR_MAKES as readonly string[]).includes(make) ? [...POPULAR_MAKES, make] : [...POPULAR_MAKES];
  const baseModels = make ? POPULAR_MODELS[make] ?? [] : [];
  const modelOptions =
    model && !baseModels.includes(model) ? [...baseModels, model] : baseModels;

  const clearValidationFeedback = useCallback(() => {
    setErrors({});
    setShowValidationSummary(false);
  }, []);

  const lookupVin = useCallback(
    async (vinValue: string) => {
      setVinLookupLoading(true);
      setVinValidationError(null);
      try {
        const res = await fetch('/api/vehicle-setup/vin-lookup', {
          method: 'POST',
          credentials: 'include',
          headers: buildHeaders(getAccessToken),
          body: JSON.stringify({ vin: vinValue, use_cache: true }),
        });
        if (!res.ok) {
          const msg = await readErrorMessage(res);
          setVinValidationError(
            res.status === 503
              ? 'VIN lookup is temporarily unavailable. You can still enter your vehicle details below.'
              : msg || 'VIN lookup failed. You can still enter your vehicle details below.'
          );
          setVinResolved(false);
          return;
        }
        const data = (await res.json()) as {
          success?: boolean;
          vehicle_info?: {
            year?: number;
            make?: string;
            model?: string;
            trim?: string;
          };
        };
        if (data.success && data.vehicle_info) {
          const info = data.vehicle_info;
          if (info.year) setYear(String(info.year));
          if (info.make) setMake(info.make);
          if (info.model) setModel(info.model);
          if (info.trim) setTrim(info.trim);
          setVinResolved(true);
        } else {
          setVinValidationError('VIN lookup did not return vehicle details. Enter year, make, and model below.');
          setVinResolved(false);
        }
      } catch {
        setVinValidationError('VIN lookup failed. You can still enter your vehicle details below.');
        setVinResolved(false);
      } finally {
        setVinLookupLoading(false);
      }
    },
    [getAccessToken]
  );

  const lookupMsa = useCallback(
    async (zip: string) => {
      setZipLookupLoading(true);
      setZipValidationError(null);
      try {
        const res = await fetch('/api/vehicle-setup/zipcode-to-msa', {
          method: 'POST',
          credentials: 'include',
          headers: buildHeaders(getAccessToken),
          body: JSON.stringify({ zipcode: zip }),
        });
        if (!res.ok) {
          setZipValidationError('Could not detect your area from this ZIP. You can still save.');
          return;
        }
        const data = (await res.json()) as {
          success?: boolean;
          msa_info?: { msa?: string };
        };
        if (data.success && data.msa_info?.msa) {
          setAssignedMsa(data.msa_info.msa);
        } else {
          setZipValidationError('Could not detect your area from this ZIP. You can still save.');
        }
      } catch {
        setZipValidationError('Area lookup unavailable. You can still save.');
      } finally {
        setZipLookupLoading(false);
      }
    },
    [getAccessToken]
  );

  const handleVinChange = useCallback(
    (value: string) => {
      const sanitized = value.toUpperCase().replace(/[^A-HJ-NPR-Z0-9]/g, '').slice(0, 17);
      setVin(sanitized);
      setVinValidationError(null);
      setVinResolved(false);
      if (vinDebounceRef.current) clearTimeout(vinDebounceRef.current);
      if (sanitized.length === 17) {
        vinDebounceRef.current = setTimeout(() => {
          lookupVin(sanitized);
        }, 500);
      }
    },
    [lookupVin]
  );

  const handleGarageZipChange = useCallback(
    (value: string) => {
      const sanitized = value.replace(/\D/g, '').slice(0, 5);
      setGarageZip(sanitized);
      setZipValidationError(null);
      if (zipDebounceRef.current) clearTimeout(zipDebounceRef.current);
      if (sanitized.length === 5) {
        zipDebounceRef.current = setTimeout(() => {
          lookupMsa(sanitized);
        }, 500);
      } else {
        setAssignedMsa('');
      }
    },
    [lookupMsa]
  );

  // Stage 2: Vehicle augmentation — fields lifted from VehicleSetup
  // (the dashboard reference component) into the wizard step.
  // Backend writes to existing vehicles columns that were previously
  // unpopulated for wizard users. See commit d5592292 for Stage 1 context.
  const validate = useCallback((): FieldErrors => {
    const next: FieldErrors = {};
    const vinTrimmed = vin.trim();
    if (vinTrimmed && (!VIN_REGEX.test(vinTrimmed) || vinTrimmed.length !== 17)) {
      next.vin =
        'VIN must be exactly 17 characters and contain only valid VIN characters (no I, O, or Q).';
    }
    if (!make.trim()) next.make = 'Enter make.';
    if (!model.trim()) next.model = 'Enter model.';
    const y = Number.parseInt(year, 10);
    if (!Number.isInteger(y) || y < 1980 || y > currentYear + 1) {
      next.year = `Enter a year between 1980 and ${currentYear + 1}.`;
    }
    const cm = Number.parseInt(currentMileage, 10);
    if (!Number.isInteger(cm) || cm < 0 || cm > 999999) {
      next.currentMileage = 'Current mileage is required.';
    }
    const mm = Number.parseInt(monthlyMiles, 10);
    if (!Number.isInteger(mm) || mm < 0 || mm > 10000) {
      next.monthlyMiles = 'Monthly miles driven is required.';
    }
    const zip = garageZip.trim();
    if (zip.length !== 5 || !/^\d{5}$/.test(zip)) {
      next.garageZip = 'ZIP code is required (5 digits).';
    }
    const mp = Number.parseFloat(monthlyPayment);
    if (!Number.isFinite(mp) || mp < 0) next.monthly_payment = 'Monthly payment must be 0 or greater.';
    const ins = Number.parseFloat(insuranceMonthly);
    if (!Number.isFinite(ins) || ins < 0) next.insurance_monthly = 'Insurance must be 0 or greater.';
    if (!['recent', '3-6mo', '6-12mo', 'over_year', 'unknown'].includes(lastOilChangeBucket)) {
      next.last_oil_change_bucket = 'Choose an option.';
    }
    if (!['up_to_date', 'overdue', 'scheduled', 'unknown'].includes(majorServiceStatus)) {
      next.major_service_status = 'Choose an option.';
    }
    if (knownIssues.length > 500) next.known_issues = 'Known issues must be 500 characters or fewer.';
    return next;
  }, [
    vin,
    make,
    model,
    year,
    currentMileage,
    monthlyMiles,
    garageZip,
    monthlyPayment,
    insuranceMonthly,
    lastOilChangeBucket,
    majorServiceStatus,
    knownIssues,
    currentYear,
  ]);

  const postRecurringExpense = useCallback(
    async (label: 'Car Payment' | 'Auto Insurance', amount: number) => {
      const res = await fetch('/api/transaction-schedule/expenses', {
        method: 'POST',
        credentials: 'include',
        headers: buildHeaders(getAccessToken),
        body: JSON.stringify({
          label,
          amount,
          category: 'transportation',
          frequency: 'monthly',
          due_day: 1,
          next_date: firstOfNextMonthIso(),
        }),
      });
      if (res.status !== 200 && res.status !== 201) {
        throw new Error(await readErrorMessage(res));
      }
    },
    [getAccessToken]
  );

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitBanner(null);
    const token = getAccessToken();
    if (!token) {
      setSubmitBanner('You must be signed in to save.');
      return;
    }

    setIsSubmitting(true);
    try {
      if (!hasVehicle) {
        await onSubmit({ has_vehicle: false, vehicle_count: 0, vehicles: [] });
        return;
      }

      const nextErrors = validate();
      setErrors(nextErrors);
      const order: Field[] = [
        'vin',
        'make',
        'model',
        'year',
        'currentMileage',
        'monthlyMiles',
        'garageZip',
        'monthly_payment',
        'insurance_monthly',
        'last_oil_change_bucket',
        'major_service_status',
        'known_issues',
      ];
      const firstInvalid = order.find((f) => nextErrors[f]);
      if (firstInvalid) {
        setShowValidationSummary(true);
        const el = document.getElementById(`vehicle-${firstInvalid}`);
        el?.focus();
        return;
      }

      setShowValidationSummary(false);
      const parsedYear = Number.parseInt(year, 10);
      const parsedCurrentMileage = Number.parseInt(currentMileage, 10);
      const parsedMonthlyMiles = Number.parseInt(monthlyMiles, 10);
      const parsedPayment = Number.parseFloat(monthlyPayment);
      const parsedInsurance = Number.parseFloat(insuranceMonthly);
      const fuelTrimmed = monthlyFuel.trim();
      const parsedFuel = fuelTrimmed ? Number.parseFloat(fuelTrimmed) : 0;
      const monthlyFuelOut = Number.isFinite(parsedFuel) && parsedFuel > 0 ? parsedFuel : 0;
      if (parsedInsurance > 0) await postRecurringExpense('Auto Insurance', parsedInsurance);
      await onSubmit({
        has_vehicle: true,
        vehicle_count: 1,
        vehicles: [
          {
            make: make.trim(),
            model: model.trim(),
            year: parsedYear,
            vin: vin.trim() || null,
            trim: trim.trim() || null,
            current_mileage: parsedCurrentMileage,
            monthly_miles: parsedMonthlyMiles,
            user_zipcode: garageZip.trim(),
            assigned_msa: assignedMsa.trim() || null,
            monthly_payment: parsedPayment,
            monthly_fuel: monthlyFuelOut,
            recent_maintenance:
              lastOilChangeBucket === 'recent' || majorServiceStatus === 'up_to_date',
          },
        ],
      });
    } catch (err) {
      setSubmitBanner(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h1 className="font-serif text-2xl font-semibold text-[#1E293B] sm:text-3xl">Vehicle</h1>
        <p className="mt-2 text-sm text-[#64748B]">
          Add your vehicle details so we can project transportation costs and maintenance risk.
        </p>

        {showValidationSummary && Object.keys(errors).length > 0 && (
          <div
            className="relative mt-4 rounded-lg border border-red-700 bg-red-600 px-4 py-3 text-sm text-white"
            role="alert"
          >
            Please fix the highlighted errors below before continuing.
          </div>
        )}
        {submitBanner && (
          <div
            className="relative mt-4 rounded-lg border border-red-700 bg-red-600 px-4 py-3 text-sm text-white"
            role="alert"
          >
            <button
              type="button"
              className="absolute right-2 top-2 rounded p-1 text-white hover:bg-red-700"
              aria-label="Dismiss error"
              onClick={() => setSubmitBanner(null)}
            >
              ×
            </button>
            <span className="pr-8">{submitBanner}</span>
          </div>
        )}

        <div className="mt-6 space-y-4">
          <fieldset>
            <legend className={labelClass}>Do you currently have a vehicle?</legend>
            <div className="flex gap-4 text-sm text-[#1E293B]">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={hasVehicle}
                  onChange={() => {
                    clearValidationFeedback();
                    setHasVehicle(true);
                  }}
                />
                Yes
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={!hasVehicle}
                  onChange={() => {
                    clearValidationFeedback();
                    setHasVehicle(false);
                  }}
                />
                No
              </label>
            </div>
          </fieldset>

          {hasVehicle && (
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className={labelClass} htmlFor="vehicle-vin">
                  Vehicle Identification Number (VIN) — optional
                </label>
                <p className={helperClass}>
                  Entering your VIN gives us more accurate vehicle data — year, make, model, and trim
                  auto-fill.
                </p>
                <div className="relative mt-1.5">
                  <input
                    id="vehicle-vin"
                    className={`${inputClass} font-mono text-sm`}
                    type="text"
                    maxLength={17}
                    value={vin}
                    onChange={(e) => {
                      clearValidationFeedback();
                      handleVinChange(e.target.value);
                    }}
                    placeholder="17-character VIN"
                    aria-invalid={!!errors.vin || !!vinValidationError}
                  />
                  {vinLookupLoading && (
                    <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[#64748B]">
                      Looking up…
                    </span>
                  )}
                </div>
                {errors.vin && <p className="mt-1 text-sm text-red-600">{errors.vin}</p>}
                {vinValidationError && !errors.vin && (
                  <p className="mt-1 text-sm text-amber-700">{vinValidationError}</p>
                )}
                {vinResolved && !vinValidationError && (
                  <p className="mt-1 text-sm text-green-700">Vehicle details filled from VIN.</p>
                )}
              </div>

              <div>
                <label className={labelClass} htmlFor="vehicle-year">
                  Year *
                </label>
                <select
                  id="vehicle-year"
                  className={inputClass}
                  value={year}
                  onChange={(e) => {
                    clearValidationFeedback();
                    setYear(e.target.value);
                    setVinResolved(false);
                  }}
                >
                  <option value="">Select year</option>
                  {YEARS.map((y) => (
                    <option key={y} value={y}>
                      {y}
                    </option>
                  ))}
                </select>
                {errors.year && <p className="mt-1 text-sm text-red-600">{errors.year}</p>}
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-make">
                  Make *
                </label>
                <select
                  id="vehicle-make"
                  className={inputClass}
                  value={make}
                  onChange={(e) => {
                    clearValidationFeedback();
                    setMake(e.target.value);
                    setModel('');
                    setVinResolved(false);
                  }}
                >
                  <option value="">Select make</option>
                  {makeOptions.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
                {errors.make && <p className="mt-1 text-sm text-red-600">{errors.make}</p>}
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-model">
                  Model *
                </label>
                <select
                  id="vehicle-model"
                  className={inputClass}
                  value={model}
                  disabled={!make}
                  onChange={(e) => {
                    clearValidationFeedback();
                    setModel(e.target.value);
                    setVinResolved(false);
                  }}
                >
                  <option value="">Select model</option>
                  {modelOptions.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
                {errors.model && <p className="mt-1 text-sm text-red-600">{errors.model}</p>}
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-trim">
                  Trim (optional)
                </label>
                <input
                  id="vehicle-trim"
                  className={inputClass}
                  type="text"
                  value={trim}
                  placeholder="e.g., EX, LX, Sport"
                  onChange={(e) => {
                    clearValidationFeedback();
                    setTrim(e.target.value);
                  }}
                />
              </div>

              <div>
                <label className={labelClass} htmlFor="vehicle-currentMileage">
                  Current mileage *
                </label>
                <p className={helperClass}>Your vehicle&apos;s current odometer reading.</p>
                <input
                  id="vehicle-currentMileage"
                  className={inputClass}
                  type="number"
                  min={0}
                  max={999999}
                  value={currentMileage}
                  onChange={(e) => {
                    clearValidationFeedback();
                    setCurrentMileage(e.target.value.replace(/\D/g, ''));
                  }}
                />
                {errors.currentMileage && (
                  <p className="mt-1 text-sm text-red-600">{errors.currentMileage}</p>
                )}
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-monthlyMiles">
                  Monthly miles driven *
                </label>
                <p className={helperClass}>
                  Average miles you drive per month (helps us estimate fuel and maintenance costs).
                </p>
                <input
                  id="vehicle-monthlyMiles"
                  className={inputClass}
                  type="number"
                  min={0}
                  max={10000}
                  value={monthlyMiles}
                  onChange={(e) => {
                    clearValidationFeedback();
                    setMonthlyMiles(e.target.value.replace(/\D/g, ''));
                  }}
                />
                {errors.monthlyMiles && (
                  <p className="mt-1 text-sm text-red-600">{errors.monthlyMiles}</p>
                )}
              </div>
              <div className="sm:col-span-2">
                <label className={labelClass} htmlFor="vehicle-garageZip">
                  Garage ZIP code *
                </label>
                <p className={helperClass}>
                  We use this for accurate gas, insurance, and maintenance estimates in your area.
                </p>
                <div className="relative mt-1.5">
                  <input
                    id="vehicle-garageZip"
                    className={inputClass}
                    type="text"
                    inputMode="numeric"
                    maxLength={5}
                    value={garageZip}
                    onChange={(e) => {
                      clearValidationFeedback();
                      handleGarageZipChange(e.target.value);
                    }}
                  />
                  {zipLookupLoading && (
                    <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[#64748B]">
                      Looking up…
                    </span>
                  )}
                </div>
                {errors.garageZip && <p className="mt-1 text-sm text-red-600">{errors.garageZip}</p>}
                {zipValidationError && !errors.garageZip && (
                  <p className="mt-1 text-sm text-amber-700">{zipValidationError}</p>
                )}
                {assignedMsa && !zipValidationError && (
                  <p className="mt-1 text-xs text-[#64748B]">Area detected: {assignedMsa}</p>
                )}
              </div>

              <div>
                <label className={labelClass} htmlFor="vehicle-monthly_payment">
                  Monthly payment *
                </label>
                <input
                  id="vehicle-monthly_payment"
                  className={inputClass}
                  type="number"
                  min={0}
                  step="0.01"
                  value={monthlyPayment}
                  onChange={(e) => {
                    clearValidationFeedback();
                    setMonthlyPayment(e.target.value);
                  }}
                />
                {errors.monthly_payment && (
                  <p className="mt-1 text-sm text-red-600">{errors.monthly_payment}</p>
                )}
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-monthly_fuel">
                  Estimated monthly fuel cost (optional)
                </label>
                <input
                  id="vehicle-monthly_fuel"
                  className={inputClass}
                  type="number"
                  min={0}
                  step="0.01"
                  placeholder="e.g., 150"
                  value={monthlyFuel}
                  onChange={(e) => {
                    clearValidationFeedback();
                    setMonthlyFuel(e.target.value);
                  }}
                />
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-insurance_monthly">
                  Insurance monthly *
                </label>
                <input
                  id="vehicle-insurance_monthly"
                  className={inputClass}
                  type="number"
                  min={0}
                  step="0.01"
                  value={insuranceMonthly}
                  onChange={(e) => {
                    clearValidationFeedback();
                    setInsuranceMonthly(e.target.value);
                  }}
                />
                {errors.insurance_monthly && (
                  <p className="mt-1 text-sm text-red-600">{errors.insurance_monthly}</p>
                )}
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-last_oil_change_bucket">
                  Last oil change *
                </label>
                <select
                  id="vehicle-last_oil_change_bucket"
                  className={inputClass}
                  value={lastOilChangeBucket}
                  onChange={(e) => {
                    clearValidationFeedback();
                    setLastOilChangeBucket(e.target.value as OilBucket);
                  }}
                >
                  <option value="recent">Recent</option>
                  <option value="3-6mo">3–6 months</option>
                  <option value="6-12mo">6–12 months</option>
                  <option value="over_year">Over a year</option>
                  <option value="unknown">Unknown</option>
                </select>
              </div>
              <div>
                <label className={labelClass} htmlFor="vehicle-major_service_status">
                  Major service status *
                </label>
                <select
                  id="vehicle-major_service_status"
                  className={inputClass}
                  value={majorServiceStatus}
                  onChange={(e) => {
                    clearValidationFeedback();
                    setMajorServiceStatus(e.target.value as MajorServiceStatus);
                  }}
                >
                  <option value="up_to_date">Up to date</option>
                  <option value="overdue">Overdue</option>
                  <option value="scheduled">Scheduled</option>
                  <option value="unknown">Unknown</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className={labelClass} htmlFor="vehicle-known_issues">
                  Known issues (optional, max 500)
                </label>
                <textarea
                  id="vehicle-known_issues"
                  className={inputClass}
                  maxLength={500}
                  value={knownIssues}
                  onChange={(e) => {
                    clearValidationFeedback();
                    setKnownIssues(e.target.value);
                  }}
                />
                {errors.known_issues && (
                  <p className="mt-1 text-sm text-red-600">{errors.known_issues}</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end sm:gap-4">
        <button
          type="button"
          onClick={() => onSkip()}
          disabled={isSkipInFlight}
          className="min-h-11 w-full rounded-lg text-center text-sm text-[#64748B] hover:text-[#1E293B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto sm:px-4"
        >
          {isSkipInFlight ? 'Skipping…' : 'Skip for now'}
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="min-h-11 w-full rounded-xl bg-[#5B2D8E] py-3 font-semibold text-white transition hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B2D8E] focus-visible:ring-offset-2 disabled:opacity-50 sm:w-auto sm:min-w-[200px]"
        >
          {isSubmitting ? 'Saving…' : 'Save and continue'}
        </button>
      </div>
    </form>
  );
}
