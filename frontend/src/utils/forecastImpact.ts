export interface DailyCashflowEntry {
  date: string;
  closing_balance: number;
}

export function computeForecastImpact(
  eventDateIso: string,
  eventCost: number,
  dailyCashflow: DailyCashflowEntry[]
): 'covered' | 'tight' | 'shortfall' | null {
  if (!dailyCashflow.length || eventCost === 0) return null;
  const dateStr = eventDateIso.split('T')[0];
  const dayData = dailyCashflow.find((d) => d.date === dateStr);
  if (!dayData) return null;
  const afterEvent = dayData.closing_balance - eventCost;
  if (afterEvent > 500) return 'covered';
  if (afterEvent >= 0) return 'tight';
  return 'shortfall';
}
