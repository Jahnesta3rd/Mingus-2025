import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import StreakTracker from '../StreakTracker';
import { useAuth } from '../../hooks/useAuth';
import { useAnalytics } from '../../hooks/useAnalytics';

// Mock the hooks
jest.mock('../../hooks/useAuth');
jest.mock('../../hooks/useAnalytics');

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseAnalytics = useAnalytics as jest.MockedFunction<typeof useAnalytics>;

// Mock fetch globally
global.fetch = jest.fn();

describe('StreakTracker Component', () => {
  const mockTrackInteraction = jest.fn();
  const mockTrackError = jest.fn();

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Mock auth hook
    mockUseAuth.mockReturnValue({
      user: { id: 1, email: 'test@example.com' },
      isAuthenticated: true,
      loading: false,
      login: jest.fn(),
      logout: jest.fn()
    });

    // Mock analytics hook
    mockUseAnalytics.mockReturnValue({
      trackInteraction: mockTrackInteraction,
      trackError: mockTrackError
    });

    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => 'mock-token'),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      },
      writable: true,
    });
  });

  const mockStreakData = {
    success: true,
    data: {
      streak_data: {
        current_streak: 7,
        longest_streak: 15,
        total_days: 25,
        streak_start_date: '2024-01-01',
        last_activity_date: '2024-01-07',
        is_active: true,
        streak_type: 'daily_outlook'
      },
      milestones: [
        {
          id: 'milestone_7',
          name: 'Week Warrior',
          days_required: 7,
          description: 'Reach 7 days in a row',
          reward: 'Advanced progress tracking',
          icon: 'trophy',
          color: 'text-green-500',
          achieved: true,
          achieved_date: '2024-01-07',
          progress_percentage: 100
        },
        {
          id: 'milestone_14',
          name: 'Two Week Champion',
          days_required: 14,
          description: 'Reach 14 days in a row',
          reward: 'Priority support access',
          icon: 'shield',
          color: 'text-purple-500',
          achieved: false,
          achieved_date: null,
          progress_percentage: 50
        }
      ],
      achievements: [
        {
          id: 'first_streak',
          name: 'First Steps',
          description: 'Complete your first 3-day streak',
          icon: 'star',
          color: 'text-blue-500',
          points: 10,
          unlocked: true,
          unlocked_date: '2024-01-03',
          category: 'streak'
        },
        {
          id: 'week_warrior',
          name: 'Week Warrior',
          description: 'Maintain a 7-day streak',
          icon: 'trophy',
          color: 'text-green-500',
          points: 25,
          unlocked: true,
          unlocked_date: '2024-01-07',
          category: 'streak'
        }
      ],
      recovery_options: [],
      weekly_challenges: [
        {
          id: 'daily_checkin',
          title: 'Daily Check-in',
          description: 'Check in every day this week',
          target: 7,
          current_progress: 5,
          reward: '50 points + streak bonus',
          deadline: '2024-01-14',
          category: 'engagement',
          difficulty: 'easy'
        }
      ],
      analytics: {
        current_streak: 7,
        longest_streak: 15,
        total_achievements: 2,
        total_milestones: 1,
        engagement_score: 75.5,
        consistency_rating: 85.0,
        improvement_trend: 'improving'
      },
      tier_rewards: [
        {
          name: 'Basic Streak Tracking',
          description: 'Track your daily progress',
          unlocked: true
        }
      ]
    }
  };

  it('renders streak tracker with loading state', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockStreakData
    });

    render(<StreakTracker />);

    // Should show loading state initially
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByLabelText('Loading streak data')).toBeInTheDocument();
  });

  it('renders streak data correctly', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockStreakData
    });

    render(<StreakTracker />);

    await waitFor(() => {
      expect(screen.getByText('Streak Tracker')).toBeInTheDocument();
      expect(screen.getByText('7')).toBeInTheDocument(); // Current streak
      expect(screen.getByText('Day Streak')).toBeInTheDocument();
      expect(screen.getByText('Longest: 15 days')).toBeInTheDocument();
      expect(screen.getByText('Total: 25 days')).toBeInTheDocument();
    });
  });

  it('displays milestones correctly', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockStreakData
    });

    render(<StreakTracker />);

    await waitFor(() => {
      expect(screen.getByText('Milestones')).toBeInTheDocument();
      expect(screen.getByText('Week Warrior')).toBeInTheDocument();
      expect(screen.getByText('Two Week Champion')).toBeInTheDocument();
    });
  });

  it('shows recovery options when streak is inactive', async () => {
    const inactiveStreakData = {
      ...mockStreakData,
      data: {
        ...mockStreakData.data,
        streak_data: {
          ...mockStreakData.data.streak_data,
          is_active: false
        },
        recovery_options: [
          {
            id: 'restart',
            type: 'restart',
            title: 'Start Fresh',
            description: 'Begin a new streak from today',
            cost: null,
            available: true,
            action: 'begin_new_streak'
          }
        ]
      }
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => inactiveStreakData
    });

    render(<StreakTracker showRecoveryOptions={true} />);

    await waitFor(() => {
      expect(screen.getByText('Recovery Options')).toBeInTheDocument();
    });
  });

  it('handles achievements panel', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockStreakData
    });

    render(<StreakTracker showAchievements={true} />);

    await waitFor(() => {
      const achievementsButton = screen.getByText('Achievements');
      expect(achievementsButton).toBeInTheDocument();
      
      fireEvent.click(achievementsButton);
      
      expect(screen.getByText('First Steps')).toBeInTheDocument();
      expect(screen.getByText('Week Warrior')).toBeInTheDocument();
    });
  });

  it('handles weekly challenges panel', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockStreakData
    });

    render(<StreakTracker showWeeklyChallenges={true} />);

    await waitFor(() => {
      const challengesButton = screen.getByText('Challenges');
      expect(challengesButton).toBeInTheDocument();
      
      fireEvent.click(challengesButton);
      
      expect(screen.getByText('Daily Check-in')).toBeInTheDocument();
      expect(screen.getByText('Check in every day this week')).toBeInTheDocument();
    });
  });

  it('handles error state', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<StreakTracker />);

    await waitFor(() => {
      expect(screen.getByText('Unable to Load Streak Data')).toBeInTheDocument();
      expect(screen.getByText('Network error')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
  });

  it('handles recovery action', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStreakData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

    render(<StreakTracker showRecoveryOptions={true} />);

    await waitFor(() => {
      const recoveryButton = screen.getByText('Recovery Options');
      fireEvent.click(recoveryButton);
    });

    // Test recovery action would be implemented here
  });

  it('handles social sharing', async () => {
    // Mock navigator.share
    Object.defineProperty(navigator, 'share', {
      value: jest.fn().mockResolvedValue(undefined),
      writable: true,
    });

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockStreakData
    });

    render(<StreakTracker />);

    await waitFor(() => {
      const shareButton = screen.getByText('Share');
      fireEvent.click(shareButton);
    });

    expect(navigator.share).toHaveBeenCalledWith({
      title: 'My Streak Progress',
      text: "I'm on a 7 day streak! 🔥",
      url: window.location.href,
    });
  });

  it('renders in compact mode', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockStreakData
    });

    render(<StreakTracker compact={true} />);

    await waitFor(() => {
      expect(screen.getByText('Streak Tracker')).toBeInTheDocument();
      expect(screen.getByText('7')).toBeInTheDocument();
      // In compact mode, milestones should not be shown
      expect(screen.queryByText('Milestones')).not.toBeInTheDocument();
    });
  });

  it('tracks analytics interactions', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockStreakData
    });

    render(<StreakTracker />);

    await waitFor(() => {
      expect(mockTrackInteraction).toHaveBeenCalledWith('streak_data_loaded', {
        current_streak: 7,
        total_achievements: 2
      });
    });
  });
});
