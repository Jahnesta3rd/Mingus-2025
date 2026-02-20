import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FinancialForecastTab from '../FinancialForecastTab';

const todayStr = new Date().toISOString().slice(0, 10);
const date30 = new Date();
date30.setDate(date30.getDate() + 30);
const date30Str = date30.toISOString().slice(0, 10);

function makeDailyCashflow(overrides: { opening?: number; closing30?: number; status?: 'healthy' | 'warning' | 'danger' } = {}) {
  const opening = overrides.opening ?? 5000;
  const closing30 = overrides.closing30 ?? 5320;
  const status = overrides.status ?? 'healthy';
  const entries: Array<{ date: string; opening_balance: number; closing_balance: number; net_change: number; balance_status: 'healthy' | 'warning' | 'danger' }> = [];
  for (let i = 0; i < 90; i++) {
    const d = new Date();
    d.setDate(d.getDate() + i);
    const date = d.toISOString().slice(0, 10);
    const isFirst = i === 0;
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

const mockFetch = jest.fn();

beforeEach(() => {
  mockFetch.mockReset();
  global.fetch = mockFetch;
  Object.defineProperty(window, 'localStorage', {
    value: { getItem: jest.fn(() => null) },
    writable: true,
  });
});

describe('FinancialForecastTab', () => {
  describe('1. All 3 summary cards render with correct values from API data', () => {
    it('displays Today’s Balance, 30-Day Forecast, and Balance Status from daily_cashflow', async () => {
      const daily = makeDailyCashflow({ opening: 4250, closing30: 4600, status: 'healthy' });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          forecast: {
            daily_cashflow: daily,
            monthly_summaries: [],
            vehicle_expense_totals: { total: 0, routine: 0, repair: 0 },
          },
        }),
      });

      render(<FinancialForecastTab userEmail="u@test.com" userTier="mid" />);
      await waitFor(() => expect(screen.getByText(/Today's Balance/i)).toBeInTheDocument());

      expect(screen.getByText('$4,250.00')).toBeInTheDocument();
      expect(screen.getByText('$4,600.00')).toBeInTheDocument();
      expect(screen.getByText('ON TRACK')).toBeInTheDocument();
    });
  });

  describe('2. Net change arrow is green for positive, red for negative', () => {
    it('uses green text and ▲ when net change is positive', async () => {
      const daily = makeDailyCashflow({ opening: 4000, closing30: 4500 });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          forecast: { daily_cashflow: daily, monthly_summaries: [], vehicle_expense_totals: null },
        }),
      });

      render(<FinancialForecastTab userEmail="u@test.com" userTier="mid" />);
      await waitFor(() => expect(screen.getByText(/30-Day Forecast/i)).toBeInTheDocument());

      const netLabel = screen.getByText(/from today/);
      expect(netLabel).toHaveClass('text-green-600');
      expect(netLabel.textContent).toMatch(/▲/);
    });

    it('uses red text and ▼ when net change is negative', async () => {
      const daily = makeDailyCashflow({ opening: 5000, closing30: 4500 });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          forecast: { daily_cashflow: daily, monthly_summaries: [], vehicle_expense_totals: null },
        }),
      });

      render(<FinancialForecastTab userEmail="u@test.com" userTier="mid" />);
      await waitFor(() => expect(screen.getByText(/30-Day Forecast/i)).toBeInTheDocument());

      const netLabel = screen.getByText(/from today/);
      expect(netLabel).toHaveClass('text-red-600');
      expect(netLabel.textContent).toMatch(/▼/);
    });
  });

  describe('3. Budget tier sees the locked upgrade card below the summary cards', () => {
    it('shows upgrade card for budget tier', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          forecast: {
            daily_cashflow: makeDailyCashflow(),
            monthly_summaries: [],
            vehicle_expense_totals: null,
          },
        }),
      });

      render(<FinancialForecastTab userEmail="u@test.com" userTier="budget" />);
      await waitFor(() => expect(screen.getByText(/Upgrade to Mid-tier/)).toBeInTheDocument());

      expect(screen.getByText(/Upgrade to Mid-tier to see your 90-day forecast chart/)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /View Plans/i })).toHaveAttribute('href', '/#pricing');
    });

    it('does not show upgrade card for mid tier', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          forecast: {
            daily_cashflow: makeDailyCashflow(),
            monthly_summaries: [],
            vehicle_expense_totals: null,
          },
        }),
      });

      render(<FinancialForecastTab userEmail="u@test.com" userTier="mid" />);
      await waitFor(() => expect(screen.getByText('ON TRACK')).toBeInTheDocument());

      expect(screen.queryByText(/Upgrade to Mid-tier/)).not.toBeInTheDocument();
    });
  });

  describe('4. Both API calls are attempted (primary first, fallback on failure)', () => {
    it('calls primary then fallback when primary fails', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: false })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            success: true,
            forecast: {
              daily_cashflow: makeDailyCashflow(),
              monthly_summaries: [],
              vehicle_expense_totals: null,
            },
          }),
        });

      render(<FinancialForecastTab userEmail="user@test.com" userTier="mid" />);
      await waitFor(() => expect(screen.getByText('ON TRACK')).toBeInTheDocument());

      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(mockFetch).toHaveBeenNthCalledWith(
        1,
        expect.stringContaining('/api/cash-flow/enhanced-forecast/'),
        expect.any(Object)
      );
      expect(mockFetch).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining('/api/cash-flow/backward-compatibility/'),
        expect.any(Object)
      );
    });

    it('calls only primary when primary succeeds', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          forecast: {
            daily_cashflow: makeDailyCashflow(),
            monthly_summaries: [],
            vehicle_expense_totals: null,
          },
        }),
      });

      render(<FinancialForecastTab userEmail="user@test.com" userTier="mid" />);
      await waitFor(() => expect(screen.getByText('ON TRACK')).toBeInTheDocument());

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/cash-flow/enhanced-forecast/'),
        expect.any(Object)
      );
    });
  });

  describe('5. TODO comments are in place', () => {
    it('component source contains Phase 3 and Phase 4 TODO comments', () => {
      const fs = require('fs');
      const path = require('path');
      const src = fs.readFileSync(
        path.join(__dirname, '../FinancialForecastTab.tsx'),
        'utf8'
      );
      expect(src).toContain('TODO Phase 3: Insert 90-day balance chart here');
      expect(src).toContain('TODO Phase 4: Insert monthly breakdown table here');
    });
  });
});
