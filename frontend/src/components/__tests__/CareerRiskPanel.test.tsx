import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import CareerRiskPanel from '../CareerRiskPanel';
import type { CareerRiskData } from '../../types/snapshot';

function baseData(overrides: Partial<CareerRiskData> = {}): CareerRiskData {
  return {
    probability_12mo: 0.12,
    market_multiplier: 1.0,
    occupation_multiplier: 1.1,
    employer_multiplier: 1.0,
    data_source: 'user_reported',
    ...overrides,
  };
}

describe('CareerRiskPanel commitment UI', () => {
  it('renders no commitment chip when commitment_type is null', () => {
    render(<CareerRiskPanel data={baseData({ commitment_type: null })} />);

    expect(screen.queryByText(/CAREER PATH:/)).not.toBeInTheDocument();
    expect(screen.getByText('Estimated 12-month job separation probability')).toBeInTheDocument();
  });

  it('renders no commitment chip when commitment_type is unclassified', () => {
    render(<CareerRiskPanel data={baseData({ commitment_type: 'unclassified' })} />);

    expect(screen.queryByText(/CAREER PATH:/)).not.toBeInTheDocument();
  });

  it('shows gray type_1 EXPLORING chip', () => {
    render(
      <CareerRiskPanel
        data={baseData({
          commitment_type: 'type_1',
          classification_rationale: 'Irregular practice without research signals a hobby-stage commitment.',
        })}
      />,
    );

    const chip = screen.getByText('CAREER PATH: EXPLORING');
    expect(chip).toBeInTheDocument();
    expect(chip).toHaveStyle({ backgroundColor: '#F3F4F6', color: '#4B5563' });
  });

  it('shows green type_3 INVESTED chip and pipeline credit line when credit applies', () => {
    render(
      <CareerRiskPanel
        data={baseData({
          commitment_type: 'type_3',
          pipeline_credit: 4,
          classification_rationale: 'Real-world income or project signal detected — strong commitment.',
        })}
      />,
    );

    const chip = screen.getByText('CAREER PATH: INVESTED');
    expect(chip).toBeInTheDocument();
    expect(chip).toHaveStyle({ backgroundColor: '#DCFCE7', color: '#166534' });
    expect(
      screen.getByText(
        'Active skill development detected — parallel pipeline credit applied (-4 pts).',
      ),
    ).toHaveClass('text-green-800');
  });

  it('keeps baseline layout for users without commitment data', () => {
    render(<CareerRiskPanel data={baseData()} />);

    expect(screen.getByText('Career Risk')).toBeInTheDocument();
    expect(screen.getByText('12.0%')).toBeInTheDocument();
    expect(screen.getByText('Market')).toBeInTheDocument();
    expect(screen.getByText('Methodology')).toBeInTheDocument();
    expect(screen.queryByText(/CAREER PATH:/)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/parallel pipeline credit applied/),
    ).not.toBeInTheDocument();
  });
});
