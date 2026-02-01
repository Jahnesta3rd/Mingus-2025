/**
 * ExpenseQuickTagModal component tests.
 * - Modal open/close
 * - Tag selection (trigger + mood)
 * - Submit and skip
 * - Layout (mobile vs desktop via class checks)
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { ExpenseQuickTagModal } from '../ExpenseQuickTagModal';

const mockExpense = {
  id: 'exp-1',
  amount: 45,
  merchant: 'Coffee Shop',
  category: 'dining',
  date: '2025-02-01',
};

const defaultProps = {
  expense: mockExpense,
  isOpen: true,
  onClose: jest.fn(),
  onSubmit: jest.fn(),
  onSkip: jest.fn(),
};

beforeEach(() => {
  defaultProps.onClose.mockClear();
  defaultProps.onSubmit.mockClear();
  defaultProps.onSkip.mockClear();
});

describe('ExpenseQuickTagModal', () => {
  describe('modal open/close', () => {
    it('renders when isOpen is true', () => {
      render(<ExpenseQuickTagModal {...defaultProps} />);
      expect(screen.getByRole('dialog', { name: /quick tag/i })).toBeInTheDocument();
      expect(screen.getByText(/coffee shop/i)).toBeInTheDocument();
      expect(screen.getByText(/\$45|45/)).toBeInTheDocument();
    });

    it('does not render dialog when isOpen is false', () => {
      render(<ExpenseQuickTagModal {...defaultProps} isOpen={false} />);
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('calls onClose when close button clicked', () => {
      render(<ExpenseQuickTagModal {...defaultProps} />);
      const close = screen.getByRole('button', { name: /close and skip|dismiss/i });
      fireEvent.click(close);
      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  describe('tag selection', () => {
    it('selecting trigger and mood enables Save', async () => {
      render(<ExpenseQuickTagModal {...defaultProps} />);
      const impulse = screen.getByRole('button', { name: /impulse/i });
      fireEvent.click(impulse);
      const moodGreat = screen.getByRole('button', { name: /great/i });
      fireEvent.click(moodGreat);
      const save = screen.getByRole('button', { name: /save/i });
      expect(save).not.toBeDisabled();
    });

    it('trigger pills and mood buttons are present', () => {
      render(<ExpenseQuickTagModal {...defaultProps} />);
      expect(screen.getByRole('button', { name: /planned/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /impulse/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /stressed/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /great/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /okay/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /meh/i })).toBeInTheDocument();
    });
  });

  describe('submit and skip', () => {
    it('Skip button calls onSkip and onClose', () => {
      render(<ExpenseQuickTagModal {...defaultProps} />);
      const skip = screen.getByRole('button', { name: /skip tagging/i });
      fireEvent.click(skip);
      expect(defaultProps.onSkip).toHaveBeenCalled();
      expect(defaultProps.onClose).toHaveBeenCalled();
    });

    it('Save calls onSubmit with tag and then onClose', async () => {
      render(<ExpenseQuickTagModal {...defaultProps} />);
      fireEvent.click(screen.getByRole('button', { name: /planned/i }));
      fireEvent.click(screen.getByRole('button', { name: /great/i }));
      const save = screen.getByRole('button', { name: /save/i });
      fireEvent.click(save);
      await waitFor(() => {
        expect(defaultProps.onSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            expense_id: mockExpense.id,
            trigger: 'planned',
            mood_after: 'great',
          })
        );
      });
      await waitFor(() => expect(defaultProps.onClose).toHaveBeenCalled());
    });
  });

  describe('accessibility and snapshot', () => {
    it('has accessible dialog and labels', () => {
      render(<ExpenseQuickTagModal {...defaultProps} />);
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /quick tag/i })).toBeInTheDocument();
    });

    it('matches snapshot when open', () => {
      const { container } = render(<ExpenseQuickTagModal {...defaultProps} />);
      expect(container).toMatchSnapshot();
    });
  });
});
