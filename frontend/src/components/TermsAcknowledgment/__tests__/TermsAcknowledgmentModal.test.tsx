import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { TermsAcknowledgmentModal } from '../TermsAcknowledgmentModal';

function mockScrollMetrics(
  el: HTMLElement,
  opts: { scrollHeight: number; clientHeight: number; scrollTop: number },
) {
  Object.defineProperty(el, 'scrollHeight', { value: opts.scrollHeight, configurable: true });
  Object.defineProperty(el, 'clientHeight', { value: opts.clientHeight, configurable: true });
  Object.defineProperty(el, 'scrollTop', { value: opts.scrollTop, writable: true, configurable: true });
}

function scrollRegionToPercent(region: HTMLElement, percent: number) {
  const scrollHeight = 1000;
  const clientHeight = 200;
  const maxScroll = scrollHeight - clientHeight;
  const scrollTop = (percent / 100) * maxScroll;
  mockScrollMetrics(region, { scrollHeight, clientHeight, scrollTop });
  fireEvent.scroll(region);
}

describe('TermsAcknowledgmentModal', () => {
  const onAccept = jest.fn();
  const onDecline = jest.fn();

  beforeEach(() => {
    onAccept.mockClear();
    onDecline.mockClear();
    window.localStorage.clear();
    window.localStorage.setItem('auth_token', 'test-jwt');
    document.head.innerHTML = '<meta name="csrf-token" content="csrf-test" />';
    (global.fetch as jest.Mock).mockReset();
  });

  describe('render', () => {
    it('renders without crashing and shows title, subtitle, agreement, checkbox, buttons', () => {
      render(<TermsAcknowledgmentModal onAccept={onAccept} onDecline={onDecline} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 1, name: /mingus user agreement/i })).toBeInTheDocument();
      expect(document.getElementById('terms-acknowledgment-modal-subtitle')).toHaveTextContent(
        /last updated:\s*september 2025/i,
      );
      expect(screen.getByText(/please read the full agreement below/i)).toBeInTheDocument();
      expect(screen.getByRole('region', { name: /agreement text, scrollable/i })).toBeInTheDocument();
      expect(screen.getByRole('checkbox')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /decline the user agreement/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /accept the user agreement and continue/i })).toBeInTheDocument();
    });

    it('has dialog ARIA attributes (role, aria-labelledby, aria-modal)', () => {
      render(<TermsAcknowledgmentModal onAccept={onAccept} onDecline={onDecline} />);
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      const title = screen.getByRole('heading', { level: 1 });
      expect(dialog).toHaveAttribute('aria-labelledby', title.id);
      expect(title).toHaveAttribute('id', 'terms-acknowledgment-modal-title');
    });
  });

  describe('scroll detection', () => {
    it('starts with scroll hint, accept disabled until ≥95% scroll; hint hides at ≥95%', () => {
      render(<TermsAcknowledgmentModal onAccept={onAccept} onDecline={onDecline} />);

      expect(screen.getByText(/please scroll through the entire agreement/i)).toBeInTheDocument();
      const accept = screen.getByRole('button', { name: /accept the user agreement and continue/i });
      expect(accept).toBeDisabled();

      const region = screen.getByRole('region', { name: /agreement text, scrollable/i });
      scrollRegionToPercent(region as HTMLElement, 94);
      expect(screen.getByText(/please scroll through the entire agreement/i)).toBeInTheDocument();
      expect(accept).toBeDisabled();

      scrollRegionToPercent(region as HTMLElement, 95);
      expect(screen.queryByText(/please scroll through the entire agreement/i)).not.toBeInTheDocument();
      expect(accept).toBeDisabled();
    });
  });

  describe('checkbox interaction', () => {
    it('checkbox starts unchecked; accept needs scroll and checkbox', async () => {
      const user = userEvent.setup();
      render(<TermsAcknowledgmentModal onAccept={onAccept} onDecline={onDecline} />);

      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(false);

      const accept = screen.getByRole('button', { name: /accept the user agreement and continue/i });
      await user.click(checkbox);
      expect(checkbox.checked).toBe(true);
      expect(accept).toBeDisabled();

      const region = screen.getByRole('region', { name: /agreement text, scrollable/i });
      scrollRegionToPercent(region as HTMLElement, 95);
      expect(accept).not.toBeDisabled();
    });

    it('accept stays disabled when only checkbox is checked without scrolling to 95%', async () => {
      const user = userEvent.setup();
      render(<TermsAcknowledgmentModal onAccept={onAccept} onDecline={onDecline} />);
      await user.click(screen.getByRole('checkbox'));
      expect(screen.getByRole('button', { name: /accept the user agreement and continue/i })).toBeDisabled();
    });
  });

  describe('button states', () => {
    it('accept disabled when !canAccept or loading; enabled only when canAccept; labels; decline always enabled', async () => {
      const user = userEvent.setup();
      let resolveJson: (v: unknown) => void;
      const jsonPromise = new Promise((resolve) => {
        resolveJson = resolve;
      });

      (global.fetch as jest.Mock).mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 201,
          json: () => jsonPromise,
        }),
      );

      render(<TermsAcknowledgmentModal onAccept={onAccept} onDecline={onDecline} />);

      const accept = screen.getByRole('button', { name: /accept the user agreement and continue/i });
      const decline = screen.getByRole('button', { name: /decline the user agreement/i });
      expect(accept).toHaveTextContent('ACCEPT & CONTINUE');
      expect(accept).toBeDisabled();
      expect(decline).not.toBeDisabled();

      const region = screen.getByRole('region', { name: /agreement text, scrollable/i });
      scrollRegionToPercent(region as HTMLElement, 95);
      await user.click(screen.getByRole('checkbox'));
      expect(accept).not.toBeDisabled();

      await user.click(accept);
      expect(accept).toBeDisabled();
      expect(accept).toHaveTextContent('ACCEPTING...');

      await act(async () => {
        resolveJson!({ acceptedAt: '2026-01-01' });
        await jsonPromise;
      });

      await waitFor(() => expect(onAccept).toHaveBeenCalled());
    });
  });

  describe('handlers', () => {
    it('decline calls onDecline', async () => {
      const user = userEvent.setup();
      render(<TermsAcknowledgmentModal onAccept={onAccept} onDecline={onDecline} />);
      await user.click(screen.getByRole('button', { name: /decline the user agreement/i }));
      expect(onDecline).toHaveBeenCalledTimes(1);
    });

    it('await POST json before onAccept; surfaces fetch errors without calling onAccept', async () => {
      const user = userEvent.setup();
      const order: string[] = [];

      (global.fetch as jest.Mock).mockImplementation(async () => {
        order.push('fetch');
        return {
          ok: true,
          status: 201,
          json: async () => {
            order.push('json');
            return { ok: true };
          },
        };
      });

      render(
        <TermsAcknowledgmentModal
          onAccept={() => {
            order.push('onAccept');
            onAccept();
          }}
          onDecline={onDecline}
        />,
      );

      const region = screen.getByRole('region', { name: /agreement text, scrollable/i });
      scrollRegionToPercent(region as HTMLElement, 95);
      await user.click(screen.getByRole('checkbox'));
      await user.click(screen.getByRole('button', { name: /accept the user agreement and continue/i }));

      await waitFor(() => expect(order).toEqual(['fetch', 'json', 'onAccept']));
      expect(onAccept).toHaveBeenCalled();

      onAccept.mockClear();
      order.length = 0;

      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          statusText: 'Server Error',
          json: async () => ({ error: 'Server exploded' }),
        }),
      );

      await user.click(screen.getByRole('button', { name: /accept the user agreement and continue/i }));
      await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Server exploded'));
      expect(onAccept).not.toHaveBeenCalled();
    });
  });

  describe('API integration', () => {
    it('POST /api/user/agreement-acceptance with headers; 201 calls onAccept; 4xx skips onAccept', async () => {
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ acceptedAt: 'x' }),
      });

      render(<TermsAcknowledgmentModal onAccept={onAccept} onDecline={onDecline} />);
      const region = screen.getByRole('region', { name: /agreement text, scrollable/i });
      scrollRegionToPercent(region as HTMLElement, 95);
      await user.click(screen.getByRole('checkbox'));
      await user.click(screen.getByRole('button', { name: /accept the user agreement and continue/i }));

      await waitFor(() => expect(global.fetch).toHaveBeenCalled());
      const [url, init] = (global.fetch as jest.Mock).mock.calls[0];
      expect(url).toBe('/api/user/agreement-acceptance');
      expect(init.method).toBe('POST');
      const hdrs = init.headers;
      const getHeader = (k: string) =>
        typeof Headers !== 'undefined' && hdrs instanceof Headers
          ? hdrs.get(k)
          : (hdrs as Record<string, string>)[k];
      expect(getHeader('Content-Type')).toBe('application/json');
      expect(getHeader('X-CSRF-Token')).toBe('csrf-test');
      expect(getHeader('Authorization')).toBe('Bearer test-jwt');
      expect(init.credentials).toBe('include');
      expect(JSON.parse(init.body).agreementVersion).toBe('September2025');
      await waitFor(() => expect(onAccept).toHaveBeenCalled());

      onAccept.mockClear();
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 403,
        statusText: 'Forbidden',
        json: async () => ({ message: 'nope' }),
      });
      await user.click(screen.getByRole('button', { name: /accept the user agreement and continue/i }));
      await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('nope'));
      expect(onAccept).not.toHaveBeenCalled();
    });
  });

  describe('accessibility', () => {
    it('checkbox linked to label via htmlFor; interactive elements have names', () => {
      render(<TermsAcknowledgmentModal onAccept={onAccept} onDecline={onDecline} />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('id', 'terms-acknowledgment-checkbox');
      const label = document.querySelector('label[for="terms-acknowledgment-checkbox"]');
      expect(label).not.toBeNull();
      expect(label).toHaveTextContent(/i have read and agree/i);
    });

    it('keyboard: Tab order reaches checkbox and buttons; Tab from last loops to first (focus trap)', async () => {
      const user = userEvent.setup();
      render(<TermsAcknowledgmentModal onAccept={onAccept} onDecline={onDecline} />);

      const region = screen.getByRole('region', { name: /agreement text, scrollable/i });
      const checkbox = screen.getByRole('checkbox');
      const decline = screen.getByRole('button', { name: /decline the user agreement/i });
      const accept = screen.getByRole('button', { name: /accept the user agreement and continue/i });

      scrollRegionToPercent(region as HTMLElement, 95);
      await user.click(checkbox);
      expect(accept).not.toBeDisabled();

      region.focus();
      expect(document.activeElement).toBe(region);

      await user.tab();
      expect(document.activeElement).toBe(checkbox);

      await user.tab();
      expect(document.activeElement).toBe(decline);

      await user.tab();
      expect(document.activeElement).toBe(accept);

      await user.tab();
      expect(document.activeElement).toBe(region);

      await user.tab({ shift: true });
      expect(document.activeElement).toBe(accept);
    });
  });
});
