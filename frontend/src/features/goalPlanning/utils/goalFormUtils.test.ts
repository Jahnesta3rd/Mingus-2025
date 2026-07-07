import {
  buildInitialFormValues,
  formatCurrencyInput,
  generateGoalSummary,
  parseCurrencyInput,
  submitGoal,
  validateForm,
} from './goalFormUtils.js';
import { loadGoalDefinition } from '../goalDefinitions/index.ts';

describe('goalFormUtils', () => {
  describe('formatCurrencyInput', () => {
    it('formats numbers with grouping separators', () => {
      expect(formatCurrencyInput(400000)).toBe('400,000');
      expect(formatCurrencyInput('25000')).toBe('25,000');
    });

    it('returns empty string for empty values', () => {
      expect(formatCurrencyInput('')).toBe('');
      expect(formatCurrencyInput(null)).toBe('');
    });
  });

  describe('parseCurrencyInput', () => {
    it('parses formatted currency strings', () => {
      expect(parseCurrencyInput('$400,000')).toBe(400000);
      expect(parseCurrencyInput('1,500.50')).toBe(1500.5);
    });
  });

  describe('buildInitialFormValues', () => {
    it('applies field defaults from the definition', () => {
      const definition = loadGoalDefinition('home_purchase');
      const values = buildInitialFormValues(definition);

      expect(values.downPaymentPercent).toBe(20);
      expect(values.timeline).toBe(5);
    });

    it('prefills from an existing goal object', () => {
      const definition = loadGoalDefinition('car_purchase');
      const values = buildInitialFormValues(definition, {
        parameters: { carPrice: 30000, savedAmount: 2000 },
        timeline: 3,
      });

      expect(values.carPrice).toBe('30,000');
      expect(values.savedAmount).toBe('2,000');
      expect(values.timeline).toBe(3);
    });
  });

  describe('validateForm', () => {
    it('flags missing required fields', () => {
      const definition = loadGoalDefinition('home_purchase');
      const result = validateForm(definition, {
        downPaymentPercent: 20,
        timeline: 5,
      });

      expect(result.isValid).toBe(false);
      expect(result.errors.homePrice).toMatch(/required/i);
    });

    it('rejects down payment above 100%', () => {
      const definition = loadGoalDefinition('home_purchase');
      const result = validateForm(definition, {
        homePrice: '400,000',
        downPaymentPercent: 120,
        timeline: 5,
      });

      expect(result.isValid).toBe(false);
      expect(result.errors.downPaymentPercent).toMatch(/no more than 100/i);
    });
  });

  describe('submitGoal', () => {
    it('builds analyzer-compatible home purchase payload', () => {
      const goal = submitGoal('home_purchase', {
        homePrice: '400,000',
        downPaymentPercent: 20,
        timeline: 5,
        savedAmount: '25,000',
      });

      expect(goal).toEqual({
        type: 'home_purchase',
        parameters: {
          homePrice: 400000,
          downPaymentPercent: 20,
          savedAmount: 25000,
          downPaymentAmount: 25000,
        },
        timeline: 5,
        constraints: [],
      });
    });

    it('converts apartment timeline from months to years', () => {
      const goal = submitGoal('apartment_move', {
        monthlyRent: '2,500',
        movingCosts: '3,000',
        timeline: 12,
      });

      expect(goal?.timeline).toBe(1);
      expect(goal?.parameters.monthlyRent).toBe(2500);
    });
  });

  describe('generateGoalSummary', () => {
    it('describes a home purchase goal', () => {
      const summary = generateGoalSummary('home_purchase', {
        homePrice: '400,000',
        downPaymentPercent: 20,
        timeline: 5,
        savedAmount: '25,000',
      });

      expect(summary).toMatch(/Buy a home for \$400,000/);
      expect(summary).toMatch(/20%/);
      expect(summary).toMatch(/\$25,000 saved/);
    });
  });
});
