import {
  buildGoalSummaryText,
  extractTrackedExpenseCategories,
  filterExpenseSuggestions,
  formatCurrency,
  getPathEnrichment,
} from './recommendationDisplayUtils.js';

describe('recommendationDisplayUtils', () => {
  describe('formatCurrency', () => {
    it('formats numbers as USD without cents', () => {
      expect(formatCurrency(2500)).toBe('$2,500');
    });

    it('handles invalid values as zero', () => {
      expect(formatCurrency(undefined)).toBe('$0');
    });
  });

  describe('filterExpenseSuggestions', () => {
    const suggestions = [
      { suggestionId: '1', categoryId: 'dining', monthlySavings: 120 },
      { suggestionId: '2', categoryId: 'housing', monthlySavings: 400 },
      { suggestionId: '3', categoryId: 'subscriptions', monthlySavings: 45 },
    ];

    it('returns all suggestions when no tracked categories', () => {
      expect(filterExpenseSuggestions(suggestions, [])).toHaveLength(3);
    });

    it('filters to tracked categories only', () => {
      const filtered = filterExpenseSuggestions(suggestions, ['dining', 'subscriptions']);
      expect(filtered.map((item) => item.categoryId)).toEqual(['dining', 'subscriptions']);
    });
  });

  describe('getPathEnrichment', () => {
    it('merges path-specific and global suggestions', () => {
      const enrichment = getPathEnrichment(
        'expense_reduction',
        { byPathId: {}, global: { jobs: [{ jobId: 'j1', title: 'Analyst' }] } },
        { byPathId: {}, global: { gigs: [{ gigId: 'g1', title: 'Freelance' }] } },
        {
          byPathId: {
            expense_reduction: {
              suggestions: [{ suggestionId: 'e1', categoryId: 'dining', monthlySavings: 80 }],
            },
          },
          global: { suggestions: [] },
        },
        ['dining'],
      );

      expect(enrichment.jobs).toHaveLength(1);
      expect(enrichment.gigs).toHaveLength(1);
      expect(enrichment.expenses).toHaveLength(1);
      expect(enrichment.allExpensesFiltered).toBe(false);
    });

    it('flags when all expenses are filtered out', () => {
      const enrichment = getPathEnrichment(
        'expense_reduction',
        { byPathId: {}, global: null },
        { byPathId: {}, global: null },
        {
          byPathId: {
            expense_reduction: {
              suggestions: [{ suggestionId: 'e1', categoryId: 'housing', monthlySavings: 200 }],
            },
          },
          global: null,
        },
        ['dining'],
      );

      expect(enrichment.expenses).toHaveLength(0);
      expect(enrichment.allExpensesFiltered).toBe(true);
    });
  });

  describe('buildGoalSummaryText', () => {
    it('prefers analysis summary', () => {
      expect(buildGoalSummaryText(null, { summary: 'Save for a home.' })).toBe('Save for a home.');
    });

    it('falls back to goal type', () => {
      expect(buildGoalSummaryText({ type: 'home_purchase' }, null)).toMatch(/home purchase/i);
    });
  });

  describe('extractTrackedExpenseCategories', () => {
    it('returns categories with positive amounts', () => {
      const categories = extractTrackedExpenseCategories({
        recurring_expenses: {
          categories: {
            groceries: 400,
            dining: 0,
            utilities: 150,
          },
        },
      });

      expect(categories).toEqual(['groceries', 'utilities']);
    });

    it('returns empty array when data is missing', () => {
      expect(extractTrackedExpenseCategories(null)).toEqual([]);
    });
  });
});
