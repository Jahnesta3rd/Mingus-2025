/** Helpers for transaction-schedule next_date values (local calendar). */

export function daysInMonth(year: number, monthIndex0: number): number {
  return new Date(year, monthIndex0 + 1, 0).getDate();
}

/** Next ISO date (YYYY-MM-DD) for this calendar day-of-month on or after today. */
export function nextIsoDateFromDayOfMonth(dayOfMonth: number, from: Date = new Date()): string {
  const clamped = Math.min(Math.max(1, Math.floor(dayOfMonth)), 31);
  const y = from.getFullYear();
  const m = from.getMonth();
  const dim = daysInMonth(y, m);
  const d = Math.min(clamped, dim);
  let cur = new Date(y, m, d);
  cur.setHours(12, 0, 0, 0);
  const today = new Date(from.getFullYear(), from.getMonth(), from.getDate());
  today.setHours(0, 0, 0, 0);
  if (cur < today) {
    let nm = m + 1;
    let ny = y;
    if (nm > 11) {
      nm = 0;
      ny += 1;
    }
    const dim2 = daysInMonth(ny, nm);
    const d2 = Math.min(clamped, dim2);
    cur = new Date(ny, nm, d2);
    cur.setHours(12, 0, 0, 0);
  }
  return cur.toISOString().slice(0, 10);
}

/** Next pay date on or after `from` that falls on day1 or day2 (clamped per month length). */
export function nextIsoDateSemimonthly(day1: number, day2: number, from: Date = new Date()): string {
  const a = Math.min(Math.max(1, Math.floor(day1)), 31);
  const b = Math.min(Math.max(1, Math.floor(day2)), 31);
  const start = new Date(from.getFullYear(), from.getMonth(), from.getDate());
  start.setHours(0, 0, 0, 0);
  for (let i = 0; i < 370; i += 1) {
    const cand = new Date(start);
    cand.setDate(start.getDate() + i);
    const dim = daysInMonth(cand.getFullYear(), cand.getMonth());
    const m1 = Math.min(a, dim);
    const m2 = Math.min(b, dim);
    const dom = cand.getDate();
    if (dom === m1 || dom === m2) {
      return cand.toISOString().slice(0, 10);
    }
  }
  return nextIsoDateFromDayOfMonth(a, from);
}

export type ScheduleFrequency = 'weekly' | 'biweekly' | 'semimonthly' | 'monthly';
