import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';

// Import components
import AssessmentLanding from '../AssessmentLanding';
import AssessmentFlow from '../AssessmentFlow';
import AssessmentResults from '../AssessmentResults';
import AssessmentQuestion from '../AssessmentQuestion';
import ConversionModal from '../ConversionModal';

// Mock fetch
global.fetch = jest.fn();

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ assessmentType: 'ai_job_risk', assessmentId: 'test-id' }),
}));

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Test wrapper with router
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('AssessmentLanding Component', () => {
  beforeEach(() => {
    fetch.mockClear();
    mockNavigate.mockClear();
  });

  test('renders loading state initially', () => {
    render(
      <TestWrapper>
        <AssessmentLanding />
      </TestWrapper>
    );

    expect(screen.getByText('Loading assessments...')).toBeInTheDocument();
  });

  test('renders assessments grid when data is loaded', async () => {
    const mockAssessments = [
      {
        id: '1',
        type: 'ai_job_risk',
        title: 'AI Job Risk Assessment',
        description: 'Test description',
        estimated_duration_minutes: 10,
        stats: {
          total_attempts: 100,
          completed_attempts: 80,
          completion_rate: 80,
          average_score: 75,
          average_time_minutes: 8,
        },
        user_completed: false,
        attempts_remaining: 3,
      },
    ];

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ assessments: mockAssessments }),
    });

    render(
      <TestWrapper>
        <AssessmentLanding />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('AI Job Risk Assessment')).toBeInTheDocument();
    });
  });

  test('handles error state', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    render(
      <TestWrapper>
        <AssessmentLanding />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Unable to Load Assessments')).toBeInTheDocument();
    });
  });

  test('navigates to assessment when clicked', async () => {
    const mockAssessments = [
      {
        id: '1',
        type: 'ai_job_risk',
        title: 'AI Job Risk Assessment',
        description: 'Test description',
        estimated_duration_minutes: 10,
        stats: {
          total_attempts: 100,
          completed_attempts: 80,
          completion_rate: 80,
          average_score: 75,
          average_time_minutes: 8,
        },
        user_completed: false,
        attempts_remaining: 3,
      },
    ];

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ assessments: mockAssessments }),
    });

    render(
      <TestWrapper>
        <AssessmentLanding />
      </TestWrapper>
    );

    await waitFor(() => {
      const assessmentCard = screen.getByText('AI Job Risk Assessment');
      fireEvent.click(assessmentCard);
      expect(mockNavigate).toHaveBeenCalledWith('/assessments/ai_job_risk');
    });
  });
});

describe('AssessmentQuestion Component', () => {
  const mockQuestion = {
    id: 'test-question',
    type: 'text',
    text: 'What is your current job title?',
    required: true,
  };

  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  test('renders text input question', () => {
    render(
      <AssessmentQuestion
        question={mockQuestion}
        value=""
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('What is your current job title?')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  test('renders required indicator', () => {
    render(
      <AssessmentQuestion
        question={mockQuestion}
        value=""
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('*')).toBeInTheDocument();
  });

  test('renders radio button question', () => {
    const radioQuestion = {
      ...mockQuestion,
      type: 'radio',
      options: [
        { value: 'option1', label: 'Option 1' },
        { value: 'option2', label: 'Option 2' },
      ],
    };

    render(
      <AssessmentQuestion
        question={radioQuestion}
        value=""
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('Option 1')).toBeInTheDocument();
    expect(screen.getByText('Option 2')).toBeInTheDocument();
  });

  test('renders multi-select question', () => {
    const multiSelectQuestion = {
      ...mockQuestion,
      type: 'multi_select',
      options: [
        { value: 'option1', label: 'Option 1' },
        { value: 'option2', label: 'Option 2' },
      ],
    };

    render(
      <AssessmentQuestion
        question={multiSelectQuestion}
        value={[]}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('Option 1')).toBeInTheDocument();
    expect(screen.getByText('Option 2')).toBeInTheDocument();
  });

  test('displays error message', () => {
    render(
      <AssessmentQuestion
        question={mockQuestion}
        value=""
        error="This field is required"
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('This field is required')).toBeInTheDocument();
  });

  test('calls onChange when input changes', () => {
    render(
      <AssessmentQuestion
        question={mockQuestion}
        value=""
        onChange={mockOnChange}
      />
    );

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'Software Engineer' } });

    expect(mockOnChange).toHaveBeenCalledWith('Software Engineer');
  });
});

describe('AssessmentFlow Component', () => {
  beforeEach(() => {
    fetch.mockClear();
    mockNavigate.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
  });

  test('renders loading state initially', () => {
    render(
      <TestWrapper>
        <AssessmentFlow />
      </TestWrapper>
    );

    expect(screen.getByText('Loading assessment...')).toBeInTheDocument();
  });

  test('loads saved progress from localStorage', async () => {
    const savedProgress = {
      formData: { 'question1': 'answer1' },
      currentStep: 1,
      timestamp: new Date().toISOString(),
    };

    localStorageMock.getItem.mockReturnValue(JSON.stringify(savedProgress));

    const mockAssessment = {
      id: '1',
      type: 'ai_job_risk',
      title: 'AI Job Risk Assessment',
      description: 'Test description',
      questions: [
        { id: 'question1', type: 'text', text: 'Question 1', required: true },
        { id: 'question2', type: 'text', text: 'Question 2', required: true },
      ],
      estimated_duration_minutes: 10,
      version: '1.0',
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAssessment,
    });

    render(
      <TestWrapper>
        <AssessmentFlow />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Question 2')).toBeInTheDocument();
    });
  });

  test('validates required fields', async () => {
    const mockAssessment = {
      id: '1',
      type: 'ai_job_risk',
      title: 'AI Job Risk Assessment',
      description: 'Test description',
      questions: [
        { id: 'question1', type: 'text', text: 'Question 1', required: true },
      ],
      estimated_duration_minutes: 10,
      version: '1.0',
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAssessment,
    });

    render(
      <TestWrapper>
        <AssessmentFlow />
      </TestWrapper>
    );

    await waitFor(() => {
      const nextButton = screen.getByText('Next →');
      fireEvent.click(nextButton);
      expect(screen.getByText('This field is required')).toBeInTheDocument();
    });
  });

  test('submits assessment successfully', async () => {
    const mockAssessment = {
      id: '1',
      type: 'ai_job_risk',
      title: 'AI Job Risk Assessment',
      description: 'Test description',
      questions: [
        { id: 'question1', type: 'text', text: 'Question 1', required: true },
      ],
      estimated_duration_minutes: 10,
      version: '1.0',
    };

    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAssessment,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ assessment_id: 'result-id' }),
      });

    render(
      <TestWrapper>
        <AssessmentFlow />
      </TestWrapper>
    );

    await waitFor(() => {
      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: 'Test answer' } });
      
      const submitButton = screen.getByText('Submit Assessment');
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/assessments/ai_job_risk/results/result-id');
    });
  });
});

describe('AssessmentResults Component', () => {
  const mockResult = {
    id: 'result-id',
    assessment_type: 'ai_job_risk',
    score: 75,
    risk_level: 'medium',
    segment: 'tech-professional',
    product_tier: 'Premium ($20)',
    insights: ['Insight 1', 'Insight 2'],
    recommendations: ['Recommendation 1', 'Recommendation 2'],
    cost_projection: {
      amount: 5000,
      timeframe: '1 year',
      currency: 'USD',
    },
    social_comparison: {
      percentile: 65,
      total_users: 1000,
      message: 'You scored higher than 65% of users',
    },
    processing_time_ms: 45,
    conversion_offer: {
      lead_id: 'lead-1',
      lead_score: 85,
      offer_type: 'assessment_conversion',
      discount_percentage: 20,
      trial_days: 7,
      message: 'Special offer for you!',
    },
    upgrade_message: 'Get full access to all insights',
    created_at: '2024-01-01T10:00:00Z',
  };

  beforeEach(() => {
    fetch.mockClear();
    mockNavigate.mockClear();
  });

  test('renders loading state initially', () => {
    render(
      <TestWrapper>
        <AssessmentResults />
      </TestWrapper>
    );

    expect(screen.getByText('Loading your results...')).toBeInTheDocument();
  });

  test('renders results when data is loaded', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResult,
    });

    render(
      <TestWrapper>
        <AssessmentResults />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Your Assessment Results')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
      expect(screen.getByText('MEDIUM RISK')).toBeInTheDocument();
    });
  });

  test('handles error state', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    render(
      <TestWrapper>
        <AssessmentResults />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Unable to Load Results')).toBeInTheDocument();
    });
  });

  test('downloads PDF', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockResult,
      })
      .mockResolvedValueOnce({
        ok: true,
        blob: async () => new Blob(['PDF content']),
      });

    // Mock URL.createObjectURL and document.createElement
    const mockCreateElement = jest.fn();
    const mockClick = jest.fn();
    const mockAppendChild = jest.fn();
    const mockRemoveChild = jest.fn();
    
    mockCreateElement.mockReturnValue({
      click: mockClick,
      href: '',
    });
    
    document.createElement = mockCreateElement;
    document.body.appendChild = mockAppendChild;
    document.body.removeChild = mockRemoveChild;
    
    window.URL.createObjectURL = jest.fn(() => 'mock-url');
    window.URL.revokeObjectURL = jest.fn();

    render(
      <TestWrapper>
        <AssessmentResults />
      </TestWrapper>
    );

    await waitFor(() => {
      const downloadButton = screen.getByText('📄 Download PDF');
      fireEvent.click(downloadButton);
    });

    await waitFor(() => {
      expect(mockCreateElement).toHaveBeenCalledWith('a');
      expect(mockClick).toHaveBeenCalled();
    });
  });
});

describe('ConversionModal Component', () => {
  const mockAssessmentResult = {
    id: 'result-id',
    assessment_type: 'ai_job_risk',
    score: 75,
    risk_level: 'medium',
    conversion_offer: {
      lead_id: 'lead-1',
      lead_score: 85,
      offer_type: 'assessment_conversion',
      discount_percentage: 20,
      trial_days: 7,
      message: 'Special offer for you!',
    },
  };

  const mockOnClose = jest.fn();

  beforeEach(() => {
    fetch.mockClear();
    mockOnClose.mockClear();
  });

  test('renders subscription tiers', () => {
    render(
      <ConversionModal
        assessmentResult={mockAssessmentResult}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Basic Plan')).toBeInTheDocument();
    expect(screen.getByText('Premium Plan')).toBeInTheDocument();
    expect(screen.getByText('Enterprise Plan')).toBeInTheDocument();
  });

  test('displays countdown timer', () => {
    render(
      <ConversionModal
        assessmentResult={mockAssessmentResult}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Limited Time Offer')).toBeInTheDocument();
    expect(screen.getByText(/01:00:00/)).toBeInTheDocument();
  });

  test('handles payment processing', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ checkout_url: 'https://stripe.com/checkout' }),
    });

    render(
      <ConversionModal
        assessmentResult={mockAssessmentResult}
        onClose={mockOnClose}
      />
    );

    const basicPlanButton = screen.getByText(/Get Basic Plan/);
    fireEvent.click(basicPlanButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/assessments/convert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          assessment_id: 'result-id',
          subscription_tier: 'basic',
          lead_id: 'lead-1',
        }),
      });
    });
  });

  test('shows emergency offer on exit intent', () => {
    render(
      <ConversionModal
        assessmentResult={mockAssessmentResult}
        onClose={mockOnClose}
      />
    );

    // Simulate exit intent
    fireEvent.mouseLeave(document, { clientY: 0 });

    expect(screen.getByText('Wait! Special Emergency Offer')).toBeInTheDocument();
  });

  test('closes modal when backdrop is clicked', () => {
    render(
      <ConversionModal
        assessmentResult={mockAssessmentResult}
        onClose={mockOnClose}
      />
    );

    const backdrop = screen.getByRole('presentation');
    fireEvent.click(backdrop);

    expect(mockOnClose).toHaveBeenCalled();
  });
});

// Integration tests
describe('Assessment Components Integration', () => {
  test('complete assessment flow', async () => {
    // Mock all API calls
    const mockAssessments = [
      {
        id: '1',
        type: 'ai_job_risk',
        title: 'AI Job Risk Assessment',
        description: 'Test description',
        estimated_duration_minutes: 10,
        stats: {
          total_attempts: 100,
          completed_attempts: 80,
          completion_rate: 80,
          average_score: 75,
          average_time_minutes: 8,
        },
        user_completed: false,
        attempts_remaining: 3,
      },
    ];

    const mockAssessment = {
      id: '1',
      type: 'ai_job_risk',
      title: 'AI Job Risk Assessment',
      description: 'Test description',
      questions: [
        { id: 'question1', type: 'text', text: 'What is your job title?', required: true },
      ],
      estimated_duration_minutes: 10,
      version: '1.0',
    };

    const mockResult = {
      id: 'result-id',
      assessment_type: 'ai_job_risk',
      score: 75,
      risk_level: 'medium',
      segment: 'tech-professional',
      product_tier: 'Premium ($20)',
      insights: ['Insight 1'],
      recommendations: ['Recommendation 1'],
      cost_projection: {
        amount: 5000,
        timeframe: '1 year',
        currency: 'USD',
      },
      social_comparison: {
        percentile: 65,
        total_users: 1000,
        message: 'You scored higher than 65% of users',
      },
      processing_time_ms: 45,
      conversion_offer: {
        lead_id: 'lead-1',
        lead_score: 85,
        offer_type: 'assessment_conversion',
        discount_percentage: 20,
        trial_days: 7,
        message: 'Special offer for you!',
      },
      upgrade_message: 'Get full access to all insights',
      created_at: '2024-01-01T10:00:00Z',
    };

    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ assessments: mockAssessments }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAssessment,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ assessment_id: 'result-id' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockResult,
      });

    // Test the complete flow
    const { rerender } = render(
      <TestWrapper>
        <AssessmentLanding />
      </TestWrapper>
    );

    // Wait for landing page to load
    await waitFor(() => {
      expect(screen.getByText('AI Job Risk Assessment')).toBeInTheDocument();
    });

    // Click on assessment
    const assessmentCard = screen.getByText('AI Job Risk Assessment');
    fireEvent.click(assessmentCard);

    // Rerender with AssessmentFlow
    rerender(
      <TestWrapper>
        <AssessmentFlow />
      </TestWrapper>
    );

    // Wait for assessment to load
    await waitFor(() => {
      expect(screen.getByText('What is your job title?')).toBeInTheDocument();
    });

    // Answer question
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'Software Engineer' } });

    // Submit assessment
    const submitButton = screen.getByText('Submit Assessment');
    fireEvent.click(submitButton);

    // Rerender with AssessmentResults
    rerender(
      <TestWrapper>
        <AssessmentResults />
      </TestWrapper>
    );

    // Wait for results to load
    await waitFor(() => {
      expect(screen.getByText('Your Assessment Results')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
    });
  });
});
