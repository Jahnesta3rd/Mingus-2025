/**
 * Frontend Tests for AICalculatorModal Component
 * 
 * Tests include:
 * - React component rendering
 * - Form validation and submission
 * - Modal interactions and navigation
 * - Responsive design across devices
 * - User interaction flows
 * - State management
 * - Error handling
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';

// Mock the AICalculatorModal component
import AICalculatorModal from '../components/aiCalculator/AICalculatorModal';

// Mock services and hooks
jest.mock('../services/assessmentService', () => ({
  submitAssessment: jest.fn(),
  getAssessmentHistory: jest.fn(),
}));

jest.mock('../services/paymentService', () => ({
  processPayment: jest.fn(),
  getPaymentHistory: jest.fn(),
}));

jest.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'test-user-123',
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
    },
    isAuthenticated: true,
    login: jest.fn(),
    logout: jest.fn(),
  }),
}));

// Mock window.matchMedia for responsive testing
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('AICalculatorModal Component', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    assessmentType: 'job-risk' as const,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Rendering', () => {
    test('renders modal when isOpen is true', () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/AI Job Risk Calculator/i)).toBeInTheDocument();
    });

    test('does not render modal when isOpen is false', () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} isOpen={false} />
        </TestWrapper>
      );

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    test('renders correct assessment type title', () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} assessmentType="relationship-impact" />
        </TestWrapper>
      );

      expect(screen.getByText(/Relationship Impact Calculator/i)).toBeInTheDocument();
    });

    test('renders close button', () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      expect(closeButton).toBeInTheDocument();
    });

    test('renders form fields for job risk assessment', () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      // Check for form fields
      expect(screen.getByLabelText(/current salary/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/field/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/experience level/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/company size/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/location/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/industry/i)).toBeInTheDocument();
    });

    test('renders submit button', () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      expect(submitButton).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    test('shows validation error for empty required fields', async () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/current salary is required/i)).toBeInTheDocument();
        expect(screen.getByText(/field is required/i)).toBeInTheDocument();
        expect(screen.getByText(/experience level is required/i)).toBeInTheDocument();
      });
    });

    test('validates salary input format', async () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const salaryInput = screen.getByLabelText(/current salary/i);
      fireEvent.change(salaryInput, { target: { value: 'invalid-salary' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid salary/i)).toBeInTheDocument();
      });
    });

    test('validates salary range', async () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const salaryInput = screen.getByLabelText(/current salary/i);
      fireEvent.change(salaryInput, { target: { value: '0' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/salary must be greater than 0/i)).toBeInTheDocument();
      });
    });

    test('validates skills input', async () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const skillsInput = screen.getByLabelText(/skills/i);
      fireEvent.change(skillsInput, { target: { value: '' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/at least one skill is required/i)).toBeInTheDocument();
      });
    });

    test('clears validation errors when user starts typing', async () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/current salary is required/i)).toBeInTheDocument();
      });

      const salaryInput = screen.getByLabelText(/current salary/i);
      fireEvent.change(salaryInput, { target: { value: '75000' } });

      await waitFor(() => {
        expect(screen.queryByText(/current salary is required/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    test('submits form with valid data', async () => {
      const mockSubmitAssessment = jest.fn().mockResolvedValue({
        success: true,
        data: {
          overall_score: 0.65,
          risk_level: 'medium',
          recommendations: ['Learn AI skills'],
        },
      });

      // Mock the assessment service
      const { submitAssessment } = require('../services/assessmentService');
      submitAssessment.mockImplementation(mockSubmitAssessment);

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      // Fill out form
      const salaryInput = screen.getByLabelText(/current salary/i);
      const fieldSelect = screen.getByLabelText(/field/i);
      const experienceSelect = screen.getByLabelText(/experience level/i);
      const companySelect = screen.getByLabelText(/company size/i);
      const locationSelect = screen.getByLabelText(/location/i);
      const industrySelect = screen.getByLabelText(/industry/i);
      const skillsInput = screen.getByLabelText(/skills/i);

      fireEvent.change(salaryInput, { target: { value: '75000' } });
      fireEvent.change(fieldSelect, { target: { value: 'software_development' } });
      fireEvent.change(experienceSelect, { target: { value: 'mid' } });
      fireEvent.change(companySelect, { target: { value: 'large' } });
      fireEvent.change(locationSelect, { target: { value: 'urban' } });
      fireEvent.change(industrySelect, { target: { value: 'technology' } });
      fireEvent.change(skillsInput, { target: { value: 'python, javascript, react' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockSubmitAssessment).toHaveBeenCalledWith({
          current_salary: 75000,
          field: 'software_development',
          experience_level: 'mid',
          company_size: 'large',
          location: 'urban',
          industry: 'technology',
          skills: ['python', 'javascript', 'react'],
        });
      });
    });

    test('shows loading state during submission', async () => {
      const mockSubmitAssessment = jest.fn().mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      );

      const { submitAssessment } = require('../services/assessmentService');
      submitAssessment.mockImplementation(mockSubmitAssessment);

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      // Fill out form
      const salaryInput = screen.getByLabelText(/current salary/i);
      fireEvent.change(salaryInput, { target: { value: '75000' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      // Check loading state
      expect(screen.getByText(/calculating/i)).toBeInTheDocument();
      expect(submitButton).toBeDisabled();

      await waitFor(() => {
        expect(screen.queryByText(/calculating/i)).not.toBeInTheDocument();
      });
    });

    test('handles submission error', async () => {
      const mockSubmitAssessment = jest.fn().mockRejectedValue(new Error('Network error'));

      const { submitAssessment } = require('../services/assessmentService');
      submitAssessment.mockImplementation(mockSubmitAssessment);

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      // Fill out form
      const salaryInput = screen.getByLabelText(/current salary/i);
      fireEvent.change(salaryInput, { target: { value: '75000' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/an error occurred/i)).toBeInTheDocument();
      });
    });
  });

  describe('Modal Interactions', () => {
    test('calls onClose when close button is clicked', () => {
      const mockOnClose = jest.fn();

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} onClose={mockOnClose} />
        </TestWrapper>
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    test('calls onClose when clicking outside modal', () => {
      const mockOnClose = jest.fn();

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} onClose={mockOnClose} />
        </TestWrapper>
      );

      const modalOverlay = screen.getByRole('dialog').parentElement;
      fireEvent.click(modalOverlay!);

      expect(mockOnClose).toHaveBeenCalled();
    });

    test('calls onClose when pressing Escape key', () => {
      const mockOnClose = jest.fn();

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} onClose={mockOnClose} />
        </TestWrapper>
      );

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(mockOnClose).toHaveBeenCalled();
    });

    test('does not close modal when clicking inside modal content', () => {
      const mockOnClose = jest.fn();

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} onClose={mockOnClose} />
        </TestWrapper>
      );

      const modalContent = screen.getByRole('dialog');
      fireEvent.click(modalContent);

      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('Results Display', () => {
    test('displays assessment results after successful submission', async () => {
      const mockSubmitAssessment = jest.fn().mockResolvedValue({
        success: true,
        data: {
          overall_score: 0.65,
          risk_level: 'medium',
          field_multiplier: 1.2,
          confidence_interval: [0.60, 0.70],
          recommendations: ['Learn AI skills', 'Network more'],
          risk_factors: ['Automation risk', 'Skill gaps'],
        },
      });

      const { submitAssessment } = require('../services/assessmentService');
      submitAssessment.mockImplementation(mockSubmitAssessment);

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      // Fill out and submit form
      const salaryInput = screen.getByLabelText(/current salary/i);
      fireEvent.change(salaryInput, { target: { value: '75000' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/65%/i)).toBeInTheDocument();
        expect(screen.getByText(/medium risk/i)).toBeInTheDocument();
        expect(screen.getByText(/learn ai skills/i)).toBeInTheDocument();
        expect(screen.getByText(/network more/i)).toBeInTheDocument();
      });
    });

    test('displays risk level with appropriate styling', async () => {
      const mockSubmitAssessment = jest.fn().mockResolvedValue({
        success: true,
        data: {
          overall_score: 0.85,
          risk_level: 'high',
          recommendations: ['Test recommendation'],
        },
      });

      const { submitAssessment } = require('../services/assessmentService');
      submitAssessment.mockImplementation(mockSubmitAssessment);

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      // Submit form
      const salaryInput = screen.getByLabelText(/current salary/i);
      fireEvent.change(salaryInput, { target: { value: '75000' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        const riskLevelElement = screen.getByText(/high risk/i);
        expect(riskLevelElement).toHaveClass('risk-high');
      });
    });

    test('provides option to retake assessment', async () => {
      const mockSubmitAssessment = jest.fn().mockResolvedValue({
        success: true,
        data: {
          overall_score: 0.65,
          risk_level: 'medium',
          recommendations: ['Test recommendation'],
        },
      });

      const { submitAssessment } = require('../services/assessmentService');
      submitAssessment.mockImplementation(mockSubmitAssessment);

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      // Submit form
      const salaryInput = screen.getByLabelText(/current salary/i);
      fireEvent.change(salaryInput, { target: { value: '75000' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        const retakeButton = screen.getByRole('button', { name: /retake assessment/i });
        expect(retakeButton).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design', () => {
    test('adapts to mobile screen size', () => {
      // Mock mobile screen size
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        value: 375,
      });

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const modal = screen.getByRole('dialog');
      expect(modal).toHaveClass('mobile');
    });

    test('adapts to tablet screen size', () => {
      // Mock tablet screen size
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        value: 768,
      });

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const modal = screen.getByRole('dialog');
      expect(modal).toHaveClass('tablet');
    });

    test('adapts to desktop screen size', () => {
      // Mock desktop screen size
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        value: 1200,
      });

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const modal = screen.getByRole('dialog');
      expect(modal).toHaveClass('desktop');
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels', () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby');
      expect(screen.getByRole('dialog')).toHaveAttribute('aria-describedby');
    });

    test('supports keyboard navigation', () => {
      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      expect(closeButton).toHaveAttribute('tabindex', '0');
    });

    test('announces loading state to screen readers', async () => {
      const mockSubmitAssessment = jest.fn().mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      );

      const { submitAssessment } = require('../services/assessmentService');
      submitAssessment.mockImplementation(mockSubmitAssessment);

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const salaryInput = screen.getByLabelText(/current salary/i);
      fireEvent.change(salaryInput, { target: { value: '75000' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      expect(screen.getByText(/calculating/i)).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('Error Handling', () => {
    test('displays network error message', async () => {
      const mockSubmitAssessment = jest.fn().mockRejectedValue(new Error('Network error'));

      const { submitAssessment } = require('../services/assessmentService');
      submitAssessment.mockImplementation(mockSubmitAssessment);

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const salaryInput = screen.getByLabelText(/current salary/i);
      fireEvent.change(salaryInput, { target: { value: '75000' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });

    test('displays server error message', async () => {
      const mockSubmitAssessment = jest.fn().mockRejectedValue(new Error('Server error'));

      const { submitAssessment } = require('../services/assessmentService');
      submitAssessment.mockImplementation(mockSubmitAssessment);

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const salaryInput = screen.getByLabelText(/current salary/i);
      fireEvent.change(salaryInput, { target: { value: '75000' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/server error/i)).toBeInTheDocument();
      });
    });

    test('provides retry option after error', async () => {
      const mockSubmitAssessment = jest.fn().mockRejectedValue(new Error('Network error'));

      const { submitAssessment } = require('../services/assessmentService');
      submitAssessment.mockImplementation(mockSubmitAssessment);

      render(
        <TestWrapper>
          <AICalculatorModal {...defaultProps} />
        </TestWrapper>
      );

      const salaryInput = screen.getByLabelText(/current salary/i);
      fireEvent.change(salaryInput, { target: { value: '75000' } });

      const submitButton = screen.getByRole('button', { name: /calculate risk/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        const retryButton = screen.getByRole('button', { name: /retry/i });
        expect(retryButton).toBeInTheDocument();
      });
    });
  });
});
