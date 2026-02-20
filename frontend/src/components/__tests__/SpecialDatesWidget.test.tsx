import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SpecialDatesWidget, { getNextBirthdayDate, getCountdownBadge } from '../SpecialDatesWidget';

const mockFetch = jest.fn();

function mockProfileResponse(important_dates: Record<string, unknown> | null) {
  return {
    profile: { important_dates },
  };
}

beforeEach(() => {
  mockFetch.mockReset();
  // Default: cashflow request fails (no impact indicators). Tests override with mockResolvedValueOnce for profile.
  mockFetch.mockResolvedValue({ ok: false });
  global.fetch = mockFetch;
  jest.useRealTimers();
  Object.defineProperty(window, 'localStorage', {
    value: { getItem: jest.fn(() => 'mock-token') },
    writable: true,
  });
});

describe('SpecialDatesWidget', () => {
  describe('1. Past events are correctly excluded from the list', () => {
    it('excludes past events and only shows future or today', async () => {
      const today = new Date();
      const todayStr = today.toISOString().slice(0, 10);
      const past = new Date(today);
      past.setDate(past.getDate() - 10);
      const pastStr = past.toISOString().slice(0, 10);
      const future = new Date(today);
      future.setDate(future.getDate() + 5);
      const futureStr = future.toISOString().slice(0, 10);

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () =>
          mockProfileResponse({
            birthday: null,
            vacation: null,
            car_inspection: null,
            sisters_wedding: null,
            custom_events: [
              { name: 'Past event', date: pastStr, cost: 0 },
              { name: 'Future event', date: futureStr, cost: 100 },
            ],
          }),
      });

      render(<SpecialDatesWidget userId="user-1" userEmail="test@example.com" />);
      await waitFor(() => expect(screen.getByText('Future event')).toBeInTheDocument());

      expect(screen.getByText('Future event')).toBeInTheDocument();
      expect(screen.queryByText('Past event')).not.toBeInTheDocument();
    });

    it('includes event on today’s date', async () => {
      const todayStr = new Date().toISOString().slice(0, 10);
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () =>
          mockProfileResponse({
            birthday: null,
            vacation: { date: todayStr, cost: 500 },
            car_inspection: null,
            sisters_wedding: null,
          }),
      });

      render(<SpecialDatesWidget userId="user-1" userEmail="test@example.com" />);
      await waitFor(() => expect(screen.getByText('Vacation')).toBeInTheDocument());
      expect(screen.getByText('Vacation')).toBeInTheDocument();
    });
  });

  describe('2. Birthday shows the NEXT calendar occurrence, not the birth year', () => {
    it('getNextBirthdayDate returns next calendar date, not original year', () => {
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2025-07-01'));

      const next = getNextBirthdayDate('1995-04-12');
      expect(next).toBe('2026-04-12');

      const nextSameYear = getNextBirthdayDate('1990-08-15');
      expect(nextSameYear).toBe('2025-08-15');

      jest.useRealTimers();
    });

    it('widget shows Birthday when next occurrence is in the future', async () => {
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2025-01-01'));

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () =>
          mockProfileResponse({
            birthday: '1995-04-12',
            vacation: null,
            car_inspection: null,
            sisters_wedding: null,
          }),
      });

      render(<SpecialDatesWidget userId="user-1" userEmail="test@example.com" />);
      await waitFor(() => expect(screen.getByText('Birthday')).toBeInTheDocument());

      expect(screen.getByText('Birthday')).toBeInTheDocument();
      jest.useRealTimers();
    });
  });

  describe('3. Countdown colors change correctly at 7, 30, and 90 day thresholds', () => {
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2025-06-01T12:00:00Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('uses red badge for <= 7 days', () => {
      expect(getCountdownBadge('2025-06-05')).toMatchObject({ className: 'bg-red-100 text-red-800' });
      expect(getCountdownBadge('2025-06-08')).toMatchObject({ className: 'bg-red-100 text-red-800' }); // 7 days
      expect(getCountdownBadge('2025-06-09').className).not.toMatch(/red/); // 8 days -> amber
    });

    it('uses amber badge for 8–30 days', () => {
      expect(getCountdownBadge('2025-06-09')).toMatchObject({ className: 'bg-amber-100 text-amber-800' }); // 8 days
      expect(getCountdownBadge('2025-07-01')).toMatchObject({ className: 'bg-amber-100 text-amber-800' }); // 30 days
      expect(getCountdownBadge('2025-07-02').className).not.toMatch(/amber/); // 31 days -> blue
    });

    it('uses blue badge for 31–90 days', () => {
      expect(getCountdownBadge('2025-07-02')).toMatchObject({ className: 'bg-blue-100 text-blue-800' }); // 31 days
      expect(getCountdownBadge('2025-08-30')).toMatchObject({ className: 'bg-blue-100 text-blue-800' }); // 90 days
      expect(getCountdownBadge('2025-08-31').className).not.toMatch(/blue/); // 91 days -> gray
    });

    it('uses gray badge for > 90 days', () => {
      expect(getCountdownBadge('2025-09-01')).toMatchObject({ className: 'bg-gray-100 text-gray-700' });
      expect(getCountdownBadge('2026-01-01')).toMatchObject({ className: 'bg-gray-100 text-gray-700' });
    });
  });

  describe('4. The list scrolls when there are more than 4 events', () => {
    it('events list has max-height and overflow-y-auto', async () => {
      const futureBase = new Date();
      futureBase.setFullYear(futureBase.getFullYear() + 1);
      const dates = [1, 2, 3, 4, 5].map((d) => {
        const dt = new Date(futureBase);
        dt.setDate(dt.getDate() + d);
        return dt.toISOString().slice(0, 10);
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () =>
          mockProfileResponse({
            birthday: null,
            vacation: null,
            car_inspection: null,
            sisters_wedding: null,
            custom_events: dates.map((date, i) => ({ name: `Event ${i + 1}`, date, cost: 0 })),
          }),
      });

      render(<SpecialDatesWidget userId="user-1" userEmail="test@example.com" />);
      await waitFor(() => expect(screen.getByText('Event 1')).toBeInTheDocument());

      const list = document.querySelector('ul[aria-label="Events list"]');
      expect(list).toBeInTheDocument();
      expect(list?.className).toMatch(/max-h-\[320px\]|max-height/);
      expect(list?.className).toMatch(/overflow-y-auto/);

      const items = list?.querySelectorAll('li');
      expect(items?.length).toBe(5);
    });
  });

  describe('5. Empty state button links to /profile#important-dates', () => {
    it('Add Events button has href /profile#important-dates', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfileResponse(null),
      });

      render(<SpecialDatesWidget userId="user-1" userEmail="test@example.com" />);
      await waitFor(() => expect(screen.getByText(/Add your upcoming events/)).toBeInTheDocument());

      const addButton = screen.getByRole('link', { name: /Add Events/i });
      expect(addButton).toHaveAttribute('href', '/profile#important-dates');
    });

    it('footer "Edit events" link has href /profile#important-dates when events exist', async () => {
      const future = new Date();
      future.setDate(future.getDate() + 14);
      const futureStr = future.toISOString().slice(0, 10);

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () =>
          mockProfileResponse({
            birthday: null,
            vacation: { date: futureStr, cost: 0 },
            car_inspection: null,
            sisters_wedding: null,
          }),
      });

      render(<SpecialDatesWidget userId="user-1" userEmail="test@example.com" />);
      await waitFor(() => expect(screen.getByText('Vacation')).toBeInTheDocument());

      const editLink = screen.getByRole('link', { name: /Edit events in your profile/i });
      expect(editLink).toHaveAttribute('href', '/profile#important-dates');
    });
  });
});
