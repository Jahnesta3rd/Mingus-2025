import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ScenarioManagement from '../ScenarioManagement';

jest.mock('jspdf', () => ({
  __esModule: true,
  default: jest.fn().mockImplementation(() => ({
    setFontSize: jest.fn(),
    text: jest.fn(),
    save: jest.fn(),
  })),
}));

describe('ScenarioManagement smoke', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('renders dashboard UI elements', () => {
    render(
      <MemoryRouter>
        <ScenarioManagement />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: 'Scenario Management' })).toBeInTheDocument();
    expect(screen.getByText('Total Scenarios')).toBeInTheDocument();
    expect(screen.getByText('Retirement Plans')).toBeInTheDocument();
    expect(screen.getByText('Mortgage Plans')).toBeInTheDocument();
    expect(screen.getByText('Tax Plans')).toBeInTheDocument();
    expect(screen.getByLabelText('Filter by Type')).toBeInTheDocument();
    expect(screen.getByLabelText('From')).toBeInTheDocument();
    expect(screen.getByLabelText('To')).toBeInTheDocument();
    expect(screen.getByLabelText('Search')).toBeInTheDocument();
    expect(screen.getByLabelText('Sort by')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'List View' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Grid View' })).toBeInTheDocument();
    expect(
      screen.getByText('No scenarios saved yet. Go to calculators to create one.'),
    ).toBeInTheDocument();
  });
});
