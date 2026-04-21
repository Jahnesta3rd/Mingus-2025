import React from 'react';
import { render, screen, waitFor, act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import { TermsCheckGuard } from '../TermsCheckGuard';
import { useAuth } from '../../../hooks/useAuth';

jest.mock('../../../hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual<typeof import('react-router-dom')>('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

function mockScrollMetrics(
  el: HTMLElement,
  opts: { scrollHeight: number; clientHeight: number; scrollTop: number },
) {
  Object.defineProperty(el, 'scrollHeight', { value: opts.scrollHeight, configurable: true });
  Object.defineProperty(el, 'clientHeight', { value: opts.clientHeight, configurable: true });
  Object.defineProperty(el, 'scrollTop', { value: opts.scrollTop, writable: true, configurable: true });
}

function scrollAgreementTo95Percent() {
  const region = screen.getByRole('region', { name: /agreement text, scrollable/i });
  const scrollHeight = 1000;
  const clientHeight = 200;
  const maxScroll = scrollHeight - clientHeight;
  mockScrollMetrics(region as HTMLElement, {
    scrollHeight,
    clientHeight,
    scrollTop: 0.95 * maxScroll,
  });
  fireEvent.scroll(region);
}

describe('TermsCheckGuard', () => {
  beforeEach(() => {
    (useAuth as jest.Mock).mockReturnValue({ getAccessToken: () => 'test-token' });
    mockNavigate.mockClear();
    (global.fetch as jest.Mock).mockReset();
    window.localStorage.clear();
    window.localStorage.setItem('auth_token', 'test-token');
    document.head.innerHTML = '<meta name="csrf-token" content="csrf-test" />';
  });

  const renderGuard = (ui: React.ReactElement) =>
    render(<MemoryRouter initialEntries={['/dashboard']}>{ui}</MemoryRouter>);

  describe('loading state', () => {
    it('shows LoadingSpinner, no children, no modal while terms-status fetch is pending', async () => {
      let resolveFetch: (value: unknown) => void;
      const gate = new Promise((resolve) => {
        resolveFetch = resolve;
      });
      (global.fetch as jest.Mock).mockImplementationOnce(() => gate);

      renderGuard(
        <TermsCheckGuard>
          <div data-testid="protected-content">Content</div>
        </TermsCheckGuard>,
      );

      expect(screen.getByText('Loading…')).toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

      await act(async () => {
        resolveFetch!({
          ok: true,
          json: async () => ({
            accepted: true,
            acceptedVersion: 'September2025',
            currentVersion: 'September2025',
          }),
        });
      });

      await waitFor(() => expect(screen.getByTestId('protected-content')).toBeInTheDocument());
    });
  });

  describe('accepted terms', () => {
    it('renders children immediately and does not show the modal', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          accepted: true,
          acceptedVersion: 'September2025',
          currentVersion: 'September2025',
        }),
      });

      renderGuard(
        <TermsCheckGuard>
          <div data-testid="protected-content">Content</div>
        </TermsCheckGuard>,
      );

      await waitFor(() => expect(screen.getByTestId('protected-content')).toHaveTextContent('Content'));
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

      const [, init] = (global.fetch as jest.Mock).mock.calls[0];
      expect(init.method).toBe('GET');
      expect(init.headers.Authorization).toBe('Bearer test-token');
      expect(init.credentials).toBe('include');
    });
  });

  describe('not accepted terms', () => {
    it('shows TermsAcknowledgmentModal and hides children when accepted is false', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          accepted: false,
          acceptedVersion: null,
          currentVersion: 'September2025',
        }),
      });

      renderGuard(
        <TermsCheckGuard>
          <div data-testid="protected-content">Content</div>
        </TermsCheckGuard>,
      );

      await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });
  });

  describe('version mismatch', () => {
    it('shows modal for mismatch; after accept + refetch with matching versions, children render', async () => {
      const user = userEvent.setup();
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            accepted: true,
            acceptedVersion: 'August2025',
            currentVersion: 'September2025',
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 201,
          json: async () => ({ acceptedAt: '2026-01-01' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            accepted: true,
            acceptedVersion: 'September2025',
            currentVersion: 'September2025',
          }),
        });

      renderGuard(
        <TermsCheckGuard>
          <div data-testid="protected-content">Content</div>
        </TermsCheckGuard>,
      );

      await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());

      scrollAgreementTo95Percent();
      await user.click(screen.getByRole('checkbox'));
      await user.click(screen.getByRole('button', { name: /accept the user agreement and continue/i }));

      await waitFor(() => expect(screen.getByTestId('protected-content')).toBeInTheDocument());
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

      const urls = (global.fetch as jest.Mock).mock.calls.map((c) => c[0]);
      expect(urls.filter((u) => u === '/api/user/terms-status').length).toBe(2);
      expect(urls).toContain('/api/user/agreement-acceptance');
    });
  });

  describe('error handling', () => {
    it('shows error and Retry when fetch rejects (network error)', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new TypeError('Failed to fetch'));

      renderGuard(
        <TermsCheckGuard>
          <div data-testid="protected-content">Content</div>
        </TermsCheckGuard>,
      );

      expect(await screen.findByRole('alert')).toHaveTextContent(/failed to fetch/i);
      expect(screen.getByRole('button', { name: /^retry$/i })).toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('shows error and Retry; retry refetches; children not shown until success', async () => {
      const user = userEvent.setup();
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: async () => ({ error: 'Server unavailable' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            accepted: true,
            acceptedVersion: 'September2025',
            currentVersion: 'September2025',
          }),
        });

      renderGuard(
        <TermsCheckGuard>
          <div data-testid="protected-content">Content</div>
        </TermsCheckGuard>,
      );

      expect(await screen.findByRole('alert')).toHaveTextContent('Server unavailable');
      expect(screen.getByRole('button', { name: /^retry$/i })).toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

      await user.click(screen.getByRole('button', { name: /^retry$/i }));

      await waitFor(() => expect(screen.getByTestId('protected-content')).toBeInTheDocument());
    });
  });

  describe('accept flow', () => {
    it('refetches after accept; closes modal and shows children when refetch is accepted', async () => {
      const user = userEvent.setup();
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            accepted: false,
            acceptedVersion: null,
            currentVersion: 'September2025',
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 201,
          json: async () => ({ acceptedAt: '2026-01-01' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            accepted: true,
            acceptedVersion: 'September2025',
            currentVersion: 'September2025',
          }),
        });

      renderGuard(
        <TermsCheckGuard>
          <div data-testid="protected-content">Content</div>
        </TermsCheckGuard>,
      );

      await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());

      scrollAgreementTo95Percent();
      await user.click(screen.getByRole('checkbox'));
      await user.click(screen.getByRole('button', { name: /accept the user agreement and continue/i }));

      await waitFor(() => expect(screen.getByTestId('protected-content')).toBeInTheDocument());
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('keeps modal open when refetch still reports not accepted', async () => {
      const user = userEvent.setup();
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            accepted: false,
            acceptedVersion: null,
            currentVersion: 'September2025',
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 201,
          json: async () => ({ acceptedAt: '2026-01-01' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            accepted: false,
            acceptedVersion: null,
            currentVersion: 'September2025',
          }),
        });

      renderGuard(
        <TermsCheckGuard>
          <div data-testid="protected-content">Content</div>
        </TermsCheckGuard>,
      );

      await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());

      scrollAgreementTo95Percent();
      await user.click(screen.getByRole('checkbox'));
      await user.click(screen.getByRole('button', { name: /accept the user agreement and continue/i }));

      await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(3));
      await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });
  });

  describe('decline flow', () => {
    it('navigates to home on Decline; protected content never renders', async () => {
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          accepted: false,
          acceptedVersion: null,
          currentVersion: 'September2025',
        }),
      });

      renderGuard(
        <TermsCheckGuard>
          <div data-testid="protected-content">Content</div>
        </TermsCheckGuard>,
      );

      await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());
      await user.click(screen.getByRole('button', { name: /decline the user agreement/i }));

      expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true });
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('calls custom onDecline when provided instead of navigate', async () => {
      const user = userEvent.setup();
      const onDecline = jest.fn();
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          accepted: false,
          acceptedVersion: null,
          currentVersion: 'September2025',
        }),
      });

      renderGuard(
        <TermsCheckGuard onDecline={onDecline}>
          <div data-testid="protected-content">Content</div>
        </TermsCheckGuard>,
      );

      await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());
      await user.click(screen.getByRole('button', { name: /decline the user agreement/i }));

      expect(onDecline).toHaveBeenCalled();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });
});
