import {
  analyzeExpenseCategories,
  buildCombinations,
  getAllExpenseCutOptions,
  getKnowledgeBaseExpenseCuts,
  parseExpenseCutSuggestions,
  rankByImpact,
  suggestExpenseCuts,
} from './expenseReductionService';

const standardProfile = {
  expenses: 5200,
  expenseBreakdown: {
    housing: 1200,
    dining: 600,
    subscriptions: 150,
    transport: 300,
    entertainment: 200,
    insurance: 250,
    groceries: 400,
    utilities: 300,
  },
};

const leanProfile = {
  expenses: 3200,
  expenseBreakdown: {
    housing: 900,
    dining: 250,
    subscriptions: 80,
    transport: 180,
    entertainment: 100,
    insurance: 180,
    groceries: 300,
    utilities: 210,
  },
};

const highSpenderProfile = {
  expenses: 8500,
  expenseBreakdown: {
    housing: 2800,
    dining: 900,
    subscriptions: 250,
    transport: 500,
    entertainment: 400,
    insurance: 350,
    groceries: 600,
    utilities: 450,
  },
};

describe('analyzeExpenseCategories', () => {
  it('uses explicit expense breakdown when available', () => {
    const categories = analyzeExpenseCategories(standardProfile);
    expect(categories.find((item) => item.categoryId === 'housing')?.currentMonthly).toBe(1200);
    expect(categories.find((item) => item.categoryId === 'dining')?.currentMonthly).toBe(600);
  });

  it('allocates total expenses when breakdown is missing', () => {
    const categories = analyzeExpenseCategories({ expenses: 4000 });
    const housing = categories.find((item) => item.categoryId === 'housing');
    expect(housing?.currentMonthly).toBe(1400);
  });
});

describe('rankByImpact and buildCombinations', () => {
  it('prioritizes easy wins for small targets', () => {
    const cuts = getKnowledgeBaseExpenseCuts(standardProfile, 100);
    expect(cuts.length).toBeGreaterThan(0);
    expect(cuts[0]?.difficulty).toBe('Easy');
    const combo = buildCombinations(cuts, 100);
    expect(combo.cumulativeSavings).toBeGreaterThanOrEqual(100);
  });

  it('builds a combination to save $500/month', () => {
    const combo = buildCombinations(getAllExpenseCutOptions(standardProfile), 500);

    expect(combo.suggestions.length).toBeGreaterThanOrEqual(2);
    expect(combo.cumulativeSavings).toBeGreaterThanOrEqual(300);
    expect(combo.suggestions.every((item) => item.potentialSavings > 0)).toBe(true);
  });
});

describe('getKnowledgeBaseExpenseCuts', () => {
  it('reaches easy wins for $100/month target', () => {
    const cuts = getKnowledgeBaseExpenseCuts(standardProfile, 100);
    const total = cuts.reduce((sum, cut) => sum + cut.potentialSavings, 0);
    expect(total).toBeGreaterThanOrEqual(80);
    expect(cuts.some((cut) => cut.category === 'subscriptions')).toBe(true);
  });

  it('assembles meaningful cuts for $500/month target', () => {
    const cuts = getKnowledgeBaseExpenseCuts(standardProfile, 500);
    const total = cuts.reduce((sum, cut) => sum + cut.potentialSavings, 0);
    expect(cuts.length).toBeGreaterThanOrEqual(3);
    expect(total).toBeGreaterThanOrEqual(350);
    expect(cuts.every((cut) => cut.actionSteps.length > 0)).toBe(true);
  });

  it('handles aggressive $1000/month target with multiple categories', () => {
    const cuts = getKnowledgeBaseExpenseCuts(highSpenderProfile, 1000);
    const total = cuts.reduce((sum, cut) => sum + cut.potentialSavings, 0);
    expect(cuts.length).toBeGreaterThanOrEqual(4);
    expect(total).toBeGreaterThanOrEqual(600);
    const categories = new Set(cuts.map((cut) => cut.categoryId));
    expect(categories.size).toBeGreaterThanOrEqual(3);
  });

  it('works with lean spending profile', () => {
    const cuts = getKnowledgeBaseExpenseCuts(leanProfile, 200);
    expect(cuts.length).toBeGreaterThan(0);
    expect(cuts.every((cut) => !cut.warningFlags.some((flag) => /no food/i.test(flag)))).toBe(true);
  });

  it('never includes health-unsafe food cuts without warnings', () => {
    const cuts = getKnowledgeBaseExpenseCuts(standardProfile, 300);
    const diningCuts = cuts.filter((cut) => cut.category === 'dining' || cut.category === 'groceries');
    diningCuts.forEach((cut) => {
      if (cut.warningFlags.length > 0) {
        expect(cut.warningFlags.some((flag) => flag.includes('nutrition'))).toBe(true);
      }
    });
  });

  it('includes required suggestion fields', () => {
    const cuts = getKnowledgeBaseExpenseCuts(standardProfile, 250);
    const first = cuts[0];
    expect(first).toMatchObject({
      categoryId: expect.any(String),
      category: expect.any(String),
      suggestionId: expect.any(String),
      suggestion: expect.any(String),
      potentialSavings: expect.any(Number),
      difficulty: expect.stringMatching(/Easy|Medium|Hard/),
      impactOnLifestyle: expect.stringMatching(/None|Minor|Moderate|Significant/),
      timeline: expect.stringMatching(/Immediate|30 days|Gradual/),
    });
    expect(first?.pros.length).toBeGreaterThan(0);
    expect(first?.cons.length).toBeGreaterThan(0);
  });
});

describe('parseExpenseCutSuggestions', () => {
  it('parses fenced JSON arrays', () => {
    const payload = [{
      categoryId: 'dining',
      category: 'dining',
      suggestionId: 'test',
      suggestion: 'Cook at home',
      potentialSavings: 120,
      difficulty: 'Easy',
      impactOnLifestyle: 'Minor',
      timeline: 'Immediate',
      pros: ['Fast'],
      cons: ['Time'],
      actionSteps: ['Meal prep'],
      warningFlags: [],
    }];
    const parsed = parseExpenseCutSuggestions(`\`\`\`json\n${JSON.stringify(payload)}\n\`\`\``);
    expect(parsed).toHaveLength(1);
  });
});

describe('suggestExpenseCuts async', () => {
  it('uses mocked LLM response when available', async () => {
    const mockPayload = [{
      categoryId: 'subscriptions',
      category: 'subscriptions',
      suggestionId: 'llm_sub_cut',
      suggestion: 'Cancel duplicate streaming services',
      potentialSavings: 55,
      difficulty: 'Easy',
      impactOnLifestyle: 'None',
      timeline: 'Immediate',
      pros: ['Easy'],
      cons: ['Less content'],
      actionSteps: ['Audit subscriptions'],
      warningFlags: [],
    }];

    const result = await suggestExpenseCuts(standardProfile, 100, {
      llmClient: async () => JSON.stringify(mockPayload),
    });

    expect(result.source).toBe('llm');
    expect(result.suggestions[0]?.suggestionId).toBe('llm_sub_cut');
  });

  it('falls back to knowledge base when LLM unavailable', async () => {
    const result = await suggestExpenseCuts(standardProfile, 500, {
      llmClient: async () => null,
    });

    expect(result.source).toBe('knowledge_base');
    expect(result.suggestions.length).toBeGreaterThan(0);
    expect(result.cumulativeSavings).toBeGreaterThan(0);
  });
});
