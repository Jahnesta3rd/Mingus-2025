import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import IndependenceCostCard from '../IndependenceCostCard';
import * as independenceCostAPI from '../../api/independenceCostAPI';

jest.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    getAccessToken: () => 'test-token',
    isAuthenticated: true,
    user: { id: 'user-1', email: 'test@example.com' },
    loading: false,
  }),
}));

jest.mock('../../api/independenceCostAPI');

const mockRecommendation = {
  should_recommend: true,
  icc_assessment_id: '11111111-1111-1111-1111-111111111111',
  partner_id: '11111111-1111-1111-1111-111111111111',
  partner_name: 'Alex',
  city: 'Austin',
  monthly_cost: 2800,
  current_cost: 950,
  gap: 1850,
  startup_cost: 12000,
  message: 'Sample recommendation message',
  cta: 'Explore RFR Module',
};

const mockAssessment = {
  monthly_costs: {
    housing: 1800,
    utilities: 150,
    food: 450,
    transportation: 120,
    phone_internet: 90,
    other: 175,
    total_monthly: 2785,
  },
  startup_costs: {
    moving: 800,
    rental_deposits: 3600,
    furniture_basics: 1500,
    kitchen_appliances: 600,
    household_items: 400,
    emergency_fund: 8355,
    total_startup_cost: 15255,
    transportation: {
      car_purchase: 8000,
      car_insurance_deposit: 300,
      registration: 150,
      maintenance_fund: 1000,
    },
  },
  gap: 1850,
  timeline_months: 7,
  vibe_data: {
    emotional_scores: [8, 7, 6, 5, 4, 3, 2, 2, 2, 2, 2, 1],
    is_declining_12_weeks: true,
  },
};

describe('IndependenceCostCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (independenceCostAPI.getShouldRecommend as jest.Mock).mockResolvedValue({
      should_recommend: false,
    });
    (independenceCostAPI.getAssessment as jest.Mock).mockResolvedValue(mockAssessment);
    (independenceCostAPI.dismissCard as jest.Mock).mockResolvedValue({ success: true });
  });

  it('returns null when should_recommend is false', async () => {
    const { container } = render(<IndependenceCostCard onPurchaseClick={jest.fn()} />);
    await waitFor(() => {
      expect(independenceCostAPI.getShouldRecommend).toHaveBeenCalled();
    });
    expect(container).toBeEmptyDOMElement();
  });

  it('renders card when should_recommend is true', async () => {
    (independenceCostAPI.getShouldRecommend as jest.Mock).mockResolvedValue(mockRecommendation);

    render(<IndependenceCostCard onPurchaseClick={jest.fn()} />);

    expect(await screen.findByText(/Living independently in Austin/i)).toBeInTheDocument();
    expect(await screen.findByText(/Alex/)).toBeInTheDocument();
    expect(screen.getByText(/\$2,800/)).toBeInTheDocument();
    expect(screen.getByText(/\$1,850/)).toBeInTheDocument();
    expect(screen.getByText(/Sample recommendation message/i)).toBeInTheDocument();
  });

  it('shows loading spinner while fetching', () => {
    (independenceCostAPI.getShouldRecommend as jest.Mock).mockReturnValue(new Promise(() => {}));
    render(<IndependenceCostCard onPurchaseClick={jest.fn()} />);
    expect(screen.getByRole('status', { name: /loading independence cost recommendation/i })).toBeInTheDocument();
  });

  it('returns null on API error', async () => {
    (independenceCostAPI.getShouldRecommend as jest.Mock).mockRejectedValue(new Error('network'));
    const { container } = render(<IndependenceCostCard onPurchaseClick={jest.fn()} />);
    await waitFor(() => {
      expect(independenceCostAPI.getShouldRecommend).toHaveBeenCalled();
    });
    expect(container).toBeEmptyDOMElement();
  });

  it('calls onPurchaseClick when Explore RFR Module is clicked', async () => {
    (independenceCostAPI.getShouldRecommend as jest.Mock).mockResolvedValue(mockRecommendation);
    const onPurchaseClick = jest.fn();
    render(<IndependenceCostCard onPurchaseClick={onPurchaseClick} />);

    const button = await screen.findByRole('button', { name: /explore rfr module/i });
    await userEvent.click(button);
    expect(onPurchaseClick).toHaveBeenCalledTimes(1);
  });

  it('dismisses card after successful POST', async () => {
    (independenceCostAPI.getShouldRecommend as jest.Mock).mockResolvedValue(mockRecommendation);
    const { container } = render(<IndependenceCostCard onPurchaseClick={jest.fn()} />);

    await screen.findByText(/Alex/);
    await userEvent.click(screen.getByRole('button', { name: /dismiss/i }));

    await waitFor(() => {
      expect(independenceCostAPI.dismissCard).toHaveBeenCalled();
      expect(container).toBeEmptyDOMElement();
    });
  });

  it('shows dismiss error and keeps card when dismiss fails', async () => {
    (independenceCostAPI.getShouldRecommend as jest.Mock).mockResolvedValue(mockRecommendation);
    (independenceCostAPI.dismissCard as jest.Mock).mockRejectedValue(new Error('dismiss failed'));

    render(<IndependenceCostCard onPurchaseClick={jest.fn()} />);
    await screen.findByText(/Alex/);
    await userEvent.click(screen.getByRole('button', { name: /dismiss/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/dismiss failed/i);
    expect(screen.getByText(/Alex/)).toBeInTheDocument();
  });

  it('fetches assessment and expands breakdown on toggle', async () => {
    (independenceCostAPI.getShouldRecommend as jest.Mock).mockResolvedValue(mockRecommendation);
    render(<IndependenceCostCard onPurchaseClick={jest.fn()} />);

    await screen.findByText(/Alex/);
    await userEvent.click(screen.getByRole('button', { name: /see detailed breakdown/i }));

    await waitFor(() => {
      expect(independenceCostAPI.getAssessment).toHaveBeenCalledWith(
        mockRecommendation.partner_id,
        expect.objectContaining({ getAccessToken: expect.any(Function) }),
      );
    });

    expect(await screen.findByText(/Startup costs breakdown/i)).toBeInTheDocument();
    expect(screen.getByText(/Monthly costs breakdown/i)).toBeInTheDocument();
    expect(screen.getByText(/Steady decline over 3 months/i)).toBeInTheDocument();
    expect(screen.getByText(/8 → 7 → 6/)).toBeInTheDocument();
  });

  it('shows breakdown error when assess fails', async () => {
    (independenceCostAPI.getShouldRecommend as jest.Mock).mockResolvedValue(mockRecommendation);
    (independenceCostAPI.getAssessment as jest.Mock).mockRejectedValue(new Error('assess failed'));

    render(<IndependenceCostCard onPurchaseClick={jest.fn()} />);
    await screen.findByText(/Alex/);
    await userEvent.click(screen.getByRole('button', { name: /see detailed breakdown/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/assess failed/i);
  });
});
