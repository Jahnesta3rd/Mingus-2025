import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import FinancialForecastTab from '../FinancialForecastTab';

function renderForecastTab(props: React.ComponentProps<typeof FinancialForecastTab>) {
  return render(
    <MemoryRouter>
      <FinancialForecastTab {...props} />
    </MemoryRouter>
  );
}

const date30 = new Date();
date30.setDate(date30.getDate() + 30);
const date30Str = date30.toISOString().slice(0, 10);

function makeDailyCashflow(overrides: {
  opening?: number;
  closing30?: number;
  status?: 'healthy' | 'warning' | 'danger';
} = {}) {
  const opening = overrides.opening ?? 5000;
  const closing30 = overrides.closing30 ?? 5320;
  const status = overrides.status ?? 'healthy';
  const entries: Array<{
    date: string;
    opening_balance: number;
    closing_balance: number;
    net_change: number;
    balance_status: 'healthy' | 'warning' | 'danger';
  }> = [];
  for (let i = 0; i < 90; i++) {
    const d = new Date();
    d.setDate(d.getDate() + i);
    const date = d.toISOString().slice(0, 10);
    const is30 = date === date30Str;
    const prevClosing = i === 0 ? opening : entries[i - 1].closing_balance;
    entries.push({
      date,
      opening_balance: prevClosing,
      closing_balance: is30 ? closing30 : prevClosing + 10,
      net_change: is30 ? closing30 - prevClosing : 10,
      balance_status: status,
    });
  }
  return entries;
}

function forecastJsonBody(daily: ReturnType<typeof makeDailyCashflow>, monthlySummaries: unknown[] = []) {
  return {
    success: true,
    balance_set: true,
    forecast: {
      daily_cashflow: daily,
      monthly_summaries: monthlySummaries,
      vehicle_expense_totals: { total: 0, routine: 0, repair: 0 },
    },
  };
}

const mockFetch = jest.fn();

function urlFromFetchInput(input: RequestInfo | URL): string {
  if (typeof input === 'string') return input;
  if (typeof URL !== 'undefined' && input instanceof URL) return input.href;
  if (typeof Request !== 'undefined' && input instanceof Request) return input.url;
  return String(input);
}

/** Profile + cash-flow forecast (component fires both on mount). */
function mockFetchProfileAndForecast(
  daily: ReturnType<typeof makeDailyCashflow>,
  monthlySummaries: unknown[] = []
) {
  mockFetch.mockImplementation((input: RequestInfo | URL) => {
    const url = urlFromFetchInput(input);
    if (url.includes('/api/user/profile')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ profile: {}, current_balance: null }),
      });
    }
    if (
      url.includes('/api/cash-flow/enhanced-forecast') ||
      url.includes('/api/cash-flow/backward-compatibility')
    ) {
      return Promise.resolve({
        ok: true,
        json: async () => forecastJsonBody(daily, monthlySummaries),
      });
    }
    return Promise.resolve({
      ok: true,
      json: async () => ({}),
    });
  });
}

beforeEach(() => {
  mockFetch.mockReset();
  global.fetch = mockFetch;
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: jest.fn(() => null),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    },
    writable: true,
  });
});

describe('FinancialForecastTab', () => {
  describe('1. All 3 summary cards render with correct values from API data', () => {
    it('displays Today’s Balance, 30-Day Forecast, and Balance Status from daily_cashflow', async () => {
      const daily = makeDailyCashflow({ opening: 4250, closing30: 4600, status: 'healthy' });
      mockFetchProfileAndForecast(daily, []);

      renderForecastTab({ userEmail: 'u@test.com', userTier: 'mid' });
      await waitFor(() => expect(screen.getByText(/Today's Balance/i)).toBeInTheDocument());

      expect(screen.getByText('$4,250.00')).toBeInTheDocument();
      expect(screen.getByText('$4,600.00')).toBeInTheDocument();
      expect(screen.getByText('ON TRACK')).toBeInTheDocument();
    });
  });

  describe('2. Net change arrow is green for positive, red for negative', () => {
    it('uses green text and ▲ when net change is positive', async () => {
      const daily = makeDailyCashflow({ opening: 4000, closing30: 4500 });
      mockFetchProfileAndForecast(daily, []);

      renderForecastTab({ userEmail: 'u@test.com', userTier: 'mid' });
      await waitFor(() => expect(screen.getByText(/30-Day Forecast/i)).toBeInTheDocument());

      const netLabel = screen.getByText(/from today/);
      expect(netLabel).toHaveClass('text-green-600');
      expect(netLabel.textContent).toMatch(/▲/);
    });

    it('uses red text and ▼ when net change is negative', async () => {
      const daily = makeDailyCashflow({ opening: 5000, closing30: 4500 });
      mockFetchProfileAndForecast(daily, []);

      renderForecastTab({ userEmail: 'u@test.com', userTier: 'mid' });
      await waitFor(() => expect(screen.getByText(/30-Day Forecast/i)).toBeInTheDocument());

      const netLabel = screen.getByText(/from today/);
      expect(netLabel).toHaveClass('text-red-600');
      expect(netLabel.textContent).toMatch(/▼/);
    });
  });

  describe('3. Budget tier sees the locked upgrade card below the summary cards', () => {
    it('shows upgrade card for budget tier', async () => {
      mockFetchProfileAndForecast(makeDailyCashflow(), []);

      renderForecastTab({ userEmail: 'u@test.com', userTier: 'budget' });
      await waitFor(() =>
        expect(
          screen.getByText(/Upgrade to Mid-tier to see your 90-day forecast chart/)
        ).toBeInTheDocument()
      );

      expect(screen.getByText(/Upgrade to Mid-tier to see your 90-day forecast chart/)).toBeInTheDocument();
      const upgradeOptions = screen.getByRole('link', { name: /View upgrade options/i });
      expect(upgradeOptions).toHaveAttribute('href', '/#pricing');
      const planLinks = screen.getAllByRole('link', { name: /View Plans/i });
      expect(planLinks.length).toBeGreaterThanOrEqual(1);
      planLinks.forEach((link) => expect(link).toHaveAttribute('href', '/#pricing'));
    });

    it('does not show upgrade card for mid tier', async () => {
      mockFetchProfileAndForecast(makeDailyCashflow(), []);

      renderForecastTab({ userEmail: 'u@test.com', userTier: 'mid' });
      await waitFor(() => expect(screen.getByText('ON TRACK')).toBeInTheDocument());

      expect(screen.queryByText(/Upgrade to Mid-tier/)).not.toBeInTheDocument();
    });
  });

  describe('4. Both API calls are attempted (primary first, fallback on failure)', () => {
    it('calls primary then fallback when primary fails', async () => {
      mockFetch.mockImplementation((input: RequestInfo | URL) => {
        const url = urlFromFetchInput(input);
        if (url.includes('/api/user/profile')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ profile: {}, current_balance: null }),
          });
        }
        if (url.includes('/api/cash-flow/enhanced-forecast/')) {
          return Promise.resolve({ ok: false, status: 500 });
        }
        if (url.includes('/api/cash-flow/backward-compatibility/')) {
          return Promise.resolve({
            ok: true,
            json: async () => forecastJsonBody(makeDailyCashflow(), []),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      renderForecastTab({ userEmail: 'user@test.com', userTier: 'mid' });
      await waitFor(() => expect(screen.getByText('ON TRACK')).toBeInTheDocument());

      const urls = mockFetch.mock.calls.map((c) => urlFromFetchInput(c[0] as RequestInfo | URL));
      const enhIdx = urls.findIndex((u) => u.includes('/api/cash-flow/enhanced-forecast/'));
      const backIdx = urls.findIndex((u) => u.includes('/api/cash-flow/backward-compatibility/'));
      expect(enhIdx).toBeGreaterThanOrEqual(0);
      expect(backIdx).toBeGreaterThanOrEqual(0);
      expect(enhIdx).toBeLessThan(backIdx);
    });

    it('calls only primary forecast endpoint when primary succeeds', async () => {
      mockFetchProfileAndForecast(makeDailyCashflow(), []);

      renderForecastTab({ userEmail: 'user@test.com', userTier: 'mid' });
      await waitFor(() => expect(screen.getByText('ON TRACK')).toBeInTheDocument());

      const urls = mockFetch.mock.calls.map((c) => urlFromFetchInput(c[0] as RequestInfo | URL));
      expect(urls.some((u) => u.includes('/api/cash-flow/enhanced-forecast/'))).toBe(true);
      expect(urls.some((u) => u.includes('/api/cash-flow/backward-compatibility/'))).toBe(false);
    });
  });
});
