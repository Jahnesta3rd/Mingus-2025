import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import EnhancedCalculator from '../EnhancedCalculator';

jest.mock('jspdf', () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({
    setFontSize: jest.fn(),
    text: jest.fn(),
    save: jest.fn(),
  })),
}));

describe('EnhancedCalculator', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('renders calculator tabs and unlocks saving after calculation', () => {
    render(
      <MemoryRouter>
        <EnhancedCalculator />
      </MemoryRouter>,
    );

    expect(screen.getByText('Enhanced Calculator')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Scenario Management' })).toHaveAttribute(
      'href',
      '/scenarios',
    );

    const saveButton = screen.getByRole('button', { name: /save this scenario/i });
    expect(saveButton).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: /^calculate$/i }));

    expect(saveButton).toBeEnabled();
    expect(screen.getByText('Projected Savings')).toBeInTheDocument();
  });
});
