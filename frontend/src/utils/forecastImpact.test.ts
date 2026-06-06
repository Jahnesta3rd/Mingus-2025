import { computeForecastImpact } from './forecastImpact';

const cashflow = [
  { date: '2026-07-01', closing_balance: 1200 },
  { date: '2026-07-15', closing_balance: 400 },
  { date: '2026-07-20', closing_balance: -100 },
];

test('covered when remainder > 500', () => {
  expect(computeForecastImpact('2026-07-01', 500, cashflow)).toBe('covered');
});
test('tight when remainder 0–500', () => {
  expect(computeForecastImpact('2026-07-15', 200, cashflow)).toBe('tight');
});
test('shortfall when remainder < 0', () => {
  expect(computeForecastImpact('2026-07-20', 50, cashflow)).toBe('shortfall');
});
test('null when no row for date', () => {
  expect(computeForecastImpact('2026-08-01', 100, cashflow)).toBeNull();
});
test('null when cost is 0', () => {
  expect(computeForecastImpact('2026-07-01', 0, cashflow)).toBeNull();
});
test('null when cashflow empty', () => {
  expect(computeForecastImpact('2026-07-01', 100, [])).toBeNull();
});
