import {
  analyzeGoal,
  calculateFeasibilityScore,
  extractGoalParameters,
  generateAnalysisSummary,
  identifyChallenges,
  identifyOpportunities,
} from './goalAnalyzer';

const baseProfile = {
  id: 'user-1',
  income: 8000,
  savings: 25000,
  expenses: 5200,
  jobTitle: 'Software Engineer',
  industry: 'Technology',
  skills: ['JavaScript', 'React', 'Node.js'],
  availableHours: 8,
};

describe('extractGoalParameters', () => {
  it('merges goal type and parameters', () => {
    expect(
      extractGoalParameters({
        type: 'home_purchase',
        parameters: { homePrice: 400000 },
        timeline: 5,
      }),
    ).toEqual({
      type: 'home_purchase',
      homePrice: 400000,
    });
  });

  it('returns null for invalid goals', () => {
    expect(extractGoalParameters(null)).toBeNull();
    expect(extractGoalParameters({ parameters: { homePrice: 100 } })).toBeNull();
  });
});

describe('analyzeGoal — home affordability', () => {
  it('analyzes a home purchase goal with savings and income gaps', () => {
    const result = analyzeGoal(baseProfile, {
      type: 'home_purchase',
      parameters: { homePrice: 400000 },
      timeline: 5,
      constraints: ['max_monthly_payment'],
    });

    expect(result).not.toBeNull();
    expect(result?.goalType).toBe('home_purchase');
    expect(result?.futureState.savingsTarget).toBe(420000);
    expect(result?.gaps.savingsGap).toBe(395000);
    expect(result?.gaps.monthlyToSave).toBeCloseTo(6583.33, 1);
    expect(result?.presentState.savingsRate).toBe(35);
    expect(result?.analysis.summary).toContain('$420,000');
    expect(result?.analysis.challenges.length).toBeGreaterThan(0);
    expect(result?.analysis.opportunities.length).toBeGreaterThan(0);
    expect(result?.dataCompleteness.required).toBe(1);
  });

  it('marks an already-funded home goal as savings-ready but may still need more income', () => {
    const result = analyzeGoal(
      { ...baseProfile, savings: 500000 },
      {
        type: 'home_purchase',
        parameters: { homePrice: 400000 },
        timeline: 3,
      },
    );

    expect(result?.gaps.savingsGap).toBeLessThan(0);
    expect(result?.gaps.incomeGap).toBeGreaterThan(0);
    expect(result?.gaps.feasibilityScore).toBeGreaterThanOrEqual(40);
    expect(result?.analysis.summary).toContain('already have enough saved');
    expect(result?.analysis.challenges.some((item) => item.includes('Income'))).toBe(true);
  });
});

describe('analyzeGoal — car purchase', () => {
  it('analyzes vehicle purchase costs and expense increases', () => {
    const result = analyzeGoal(baseProfile, {
      type: 'car_purchase',
      parameters: { carPrice: 35000 },
      timeline: 2,
    });

    expect(result?.futureState.savingsTarget).toBe(38500);
    expect(result?.gaps.expenseIncrease).toBeCloseTo(233.33, 1);
    expect(result?.goalDescription).toContain('$35,000');
    expect(result?.presentState.jobTitle).toBe('Software Engineer');
  });
});

describe('analyzeGoal — apartment move', () => {
  it('analyzes move-in costs and rent-driven expense increases', () => {
    const result = analyzeGoal(
      { ...baseProfile, savings: 5000, income: 24000, expenses: 4500 },
      {
        type: 'apartment_move',
        parameters: { monthlyRent: 2200, movingCosts: 1200 },
        timeline: 1,
      },
    );

    expect(result?.futureState.savingsTarget).toBe(7800);
    expect(result?.gaps.savingsGap).toBe(2800);
    expect(result?.gaps.monthlyToSave).toBeCloseTo(233.33, 1);
    expect(result?.futureState.monthlyExpenses).toBe(6700);
    expect(result?.gaps.feasible).toBe(true);
  });
});

describe('analyzeGoal — baby planning', () => {
  it('analyzes preparation costs and ongoing expense impact', () => {
    const result = analyzeGoal(
      { ...baseProfile, savings: 10000, expenses: 5000 },
      {
        type: 'baby',
        parameters: { preparationCost: 12000 },
        timeline: 2,
      },
    );

    expect(result?.futureState.savingsTarget).toBe(12000);
    expect(result?.gaps.savingsGap).toBe(2000);
    expect(result?.gaps.expenseIncrease).toBe(1250);
    expect(result?.analysis.opportunities.some((item) => item.includes('surplus'))).toBe(true);
  });
});

describe('analyzeGoal — business startup', () => {
  it('flags income and savings constraints for a startup goal', () => {
    const result = analyzeGoal(
      { ...baseProfile, savings: 15000, income: 5000, expenses: 4200 },
      {
        type: 'business',
        parameters: { initialInvestment: 40000, monthlyCost: 3000 },
        timeline: 3,
      },
    );

    expect(result?.futureState.savingsTarget).toBe(58000);
    expect(result?.gaps.savingsGap).toBe(43000);
    expect(result?.gaps.incomeGap).toBeGreaterThan(0);
    expect(result?.gaps.feasible).toBe(false);
    expect(result?.analysis.challenges.some((item) => item.includes('Income'))).toBe(true);
    expect(result?.analysis.opportunities.some((item) => item.includes('minimum viable'))).toBe(true);
  });
});

describe('analyzeGoal — edge cases', () => {
  it('returns null for invalid goal input', () => {
    expect(analyzeGoal(baseProfile, null)).toBeNull();
    expect(
      analyzeGoal(baseProfile, {
        type: 'home_purchase',
        parameters: {},
        timeline: 5,
      }),
    ).toBeNull();
    expect(
      analyzeGoal(baseProfile, {
        type: 'home_purchase',
        parameters: { homePrice: 400000 },
        timeline: 0,
      }),
    ).toBeNull();
  });

  it('reports missing fields in data completeness', () => {
    const result = analyzeGoal(
      { id: 'sparse' },
      {
        type: 'car_purchase',
        parameters: { carPrice: 20000 },
        timeline: 2,
      },
    );

    expect(result?.dataCompleteness.missingFields).toEqual(
      expect.arrayContaining([
        'userProfile.income',
        'userProfile.savings',
        'userProfile.expenses',
      ]),
    );
    expect(result?.dataCompleteness.required).toBeLessThan(1);
  });

  it('handles aggressive timelines where monthly savings exceed income threshold', () => {
    const result = analyzeGoal(
      { ...baseProfile, savings: 0, income: 4000, expenses: 3500 },
      {
        type: 'home_purchase',
        parameters: { homePrice: 300000 },
        timeline: 1,
      },
    );

    expect(result?.gaps.feasible).toBe(false);
    expect(result?.gaps.feasibilityScore).toBeLessThan(60);
    expect(result?.analysis.challenges.some((item) => item.includes('Timeline'))).toBe(true);
  });
});

describe('helper functions', () => {
  it('generateAnalysisSummary describes savings path', () => {
    const summary = generateAnalysisSummary({
      goalDescription: 'Buy a home at $400,000',
      savingsTarget: 420000,
      timelineYears: 5,
      currentSavings: 25000,
      savingsGap: 395000,
      projectedSavingsOnCurrentPath: 193000,
    });

    expect(summary).toContain('$420,000');
    expect(summary).toContain('$193,000');
  });

  it('identifyChallenges captures multiple constraints', () => {
    const challenges = identifyChallenges({
      savingsGap: 50000,
      savingsFeasible: false,
      incomeGap: 20000,
      monthlyToSave: 4000,
      monthlyIncome: 5000,
      expenseIncrease: 900,
      savingsRate: 4,
      timelineYears: 1,
    });

    expect(challenges.some((item) => item.includes('Timeline'))).toBe(true);
    expect(challenges.some((item) => item.includes('Income'))).toBe(true);
    expect(challenges.some((item) => item.includes('savings rate'))).toBe(true);
  });

  it('identifyOpportunities suggests side income when hours are available', () => {
    const opportunities = identifyOpportunities(baseProfile, {
      incomeGap: 15000,
      savingsGap: 30000,
      savingsRate: 12,
      goalType: 'car_purchase',
    });

    expect(opportunities.some((item) => item.includes('Side income'))).toBe(true);
    expect(opportunities.some((item) => item.includes('JavaScript'))).toBe(true);
  });

  it('calculateFeasibilityScore returns 100 when goal is fully funded', () => {
    expect(
      calculateFeasibilityScore({
        savingsGap: -5000,
        savingsFeasible: true,
        incomeGap: 0,
        monthlyIncome: 8000,
        monthlyToSave: 0,
        savingsRate: 30,
      }),
    ).toBe(100);
  });
});
