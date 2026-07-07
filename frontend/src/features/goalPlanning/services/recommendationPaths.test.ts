import {
  calculateMonthlyBoostFromCareerMove,
  calculateMonthlyBoostFromExpenseCuts,
  calculateMonthlyBoostFromSideGigs,
  combinePaths,
  projectPathOverTime,
  recommendationPaths,
} from './recommendationPaths';

const baseProfile = {
  id: 'user-1',
  income: 8000,
  savings: 25000,
  expenses: 5200,
  jobTitle: 'Software Engineer',
  industry: 'Technology',
  skills: ['JavaScript', 'React', 'Node.js'],
  availableHours: 12,
};

const baseGap = {
  savingsGap: 395000,
  incomeGap: 24000,
  expenseIncrease: 167,
  monthlyToSave: 6583.33,
  feasible: false,
  feasibilityScore: 42,
};

describe('recommendation path helpers', () => {
  it('calculateMonthlyBoostFromCareerMove converts annual gap to monthly boost', () => {
    expect(calculateMonthlyBoostFromCareerMove(24000, 8000)).toBe(1500);
    expect(calculateMonthlyBoostFromCareerMove(0, 8000)).toBe(0);
  });

  it('calculateMonthlyBoostFromSideGigs scales with hours and skills', () => {
    const withSkills = calculateMonthlyBoostFromSideGigs(12, ['React', 'Node', 'TS'], 2000);
    const noSkills = calculateMonthlyBoostFromSideGigs(12, [], 5000);
    expect(withSkills).toBeGreaterThan(0);
    expect(withSkills).toBeLessThanOrEqual(2000);
    expect(noSkills).toBeLessThanOrEqual(5000);
  });

  it('calculateMonthlyBoostFromExpenseCuts caps against monthly need', () => {
    expect(calculateMonthlyBoostFromExpenseCuts(5200, 1000)).toBe(400);
    expect(calculateMonthlyBoostFromExpenseCuts(0, 1000)).toBe(0);
  });

  it('projectPathOverTime marks goalReached when target is met', () => {
    const projection = projectPathOverTime({
      startingSavings: 10000,
      savingsTarget: 30000,
      timelineYears: 2,
      monthlyBoost: 1000,
    });
    expect(projection).toHaveLength(5);
    expect(projection[1]?.goalReached).toBe(true);
  });

  it('combinePaths sums boosts and merges metadata', () => {
    const merged = combinePaths(
      [
        { pathId: 'a', monthlyBoost: 500, pros: ['Fast'], cons: ['Hard'], actionItems: ['Do A'] },
        { pathId: 'b', monthlyBoost: 300, pros: ['Easy'], cons: ['Slow'], actionItems: ['Do B'] },
      ],
      { monthlyNeeded: 1000 },
    );
    expect(merged.monthlyBoost).toBe(800);
    expect(merged.combinedPaths).toEqual(['a', 'b']);
    expect(merged.pros).toHaveLength(2);
  });
});

describe('careerAdvancement path', () => {
  it.each([
    ['home_purchase', { type: 'home_purchase', parameters: { homePrice: 400000 }, timeline: 5 }],
    ['car_purchase', { type: 'car_purchase', parameters: { carPrice: 35000 }, timeline: 2 }],
    ['business', { type: 'business', parameters: { initialInvestment: 50000, monthlyCost: 3000 }, timeline: 3 }],
  ])('builds career path for %s goals', (_label, goal) => {
    const path = recommendationPaths.careerAdvancement(baseProfile, goal, baseGap);
    expect(path?.pathId).toBe('career_advancement');
    expect(path?.monthlyBoost).toBeGreaterThan(0);
    expect(path?.projections).toHaveLength(5);
    expect(path?.action).toContain('suggestJobsForIncomeGoal');
  });
});

describe('sideIncome path', () => {
  it('returns immediate high-feasibility side income path', () => {
    const path = recommendationPaths.sideIncome(baseProfile, {
      type: 'car_purchase',
      parameters: { carPrice: 30000 },
      timeline: 2,
    }, baseGap);

    expect(path?.pathId).toBe('side_income');
    expect(path?.timeline).toBe('Immediate');
    expect(path?.feasibility).toBe('High');
    expect(path?.action).toContain('suggestSideGigs');
    expect(path?.monthlyBoost).toBeGreaterThan(0);
  });

  it('returns low feasibility when no hours are available', () => {
    const path = recommendationPaths.sideIncome(
      { ...baseProfile, availableHours: 0 },
      { type: 'baby', parameters: { preparationCost: 10000 }, timeline: 1 },
      { ...baseGap, monthlyToSave: 500 },
    );
    expect(path?.monthlyBoost).toBe(0);
    expect(path?.feasibility).toBe('Low');
  });
});

describe('expenseReduction path', () => {
  it('suggests expense cuts for apartment move goals', () => {
    const path = recommendationPaths.expenseReduction(
      { ...baseProfile, expenses: 6000 },
      { type: 'apartment_move', parameters: { monthlyRent: 2200 }, timeline: 1 },
      { savingsGap: 5000, monthlyToSave: 500, incomeGap: 10000 },
    );

    expect(path?.pathId).toBe('expense_reduction');
    expect(path?.monthlyBoost).toBe(200);
    expect(path?.action).toContain('suggestExpenseCuts');
    expect(path?.actionItems.length).toBeGreaterThan(0);
  });
});

describe('timelineExtension path', () => {
  it('extends timeline and lowers monthly savings target', () => {
    const goal = { type: 'home_purchase', parameters: { homePrice: 400000 }, timeline: 4 };
    const path = recommendationPaths.timelineExtension(goal, baseGap);

    expect(path?.pathId).toBe('timeline_extension');
    expect(path?.newTimeline).toBe(6);
    expect(path?.monthlyAfter).toBeCloseTo(4388.89, 1);
    expect(path?.monthlyBoost).toBe(0);
    expect(path?.feasibility).toBe('Very High');
    expect(path?.tradeoff).toContain('longer');
  });
});

describe('goalScopeReduction path', () => {
  it.each([
    ['car_purchase', { type: 'car_purchase', parameters: { carPrice: 35000 }, timeline: 2 }],
    ['apartment_move', { type: 'apartment_move', parameters: { monthlyRent: 2000 }, timeline: 1 }],
    ['baby', { type: 'baby', parameters: { preparationCost: 12000 }, timeline: 2 }],
  ])('returns scope options for %s', (_label, goal) => {
    const path = recommendationPaths.goalScopeReduction(goal, baseGap);
    expect(path?.pathId).toBe('goal_scope_reduction');
    expect(path?.options?.length).toBeGreaterThanOrEqual(2);
    expect(path?.tradeoff).toContain('Get less');
  });
});

describe('financing path', () => {
  it('returns mortgage option for home goals', () => {
    const path = recommendationPaths.financing(
      { type: 'home_purchase', parameters: { homePrice: 400000 }, timeline: 5 },
      baseGap,
      baseProfile,
    );

    expect(path?.pathId).toBe('financing');
    expect(path?.options?.[0]?.name).toBe('30-year mortgage');
    expect(path?.feasibility).toBe('Very High');
    expect(path?.tradeoff).toContain('interest');
  });

  it('returns auto loan option for car goals', () => {
    const path = recommendationPaths.financing(
      { type: 'car_purchase', parameters: { carPrice: 30000 }, timeline: 3 },
      { savingsGap: 10000, monthlyToSave: 300 },
      baseProfile,
    );

    expect(path?.options?.[0]?.name).toContain('Auto loan');
    expect(path?.monthlyBoost).toBeGreaterThanOrEqual(0);
  });

  it('returns business financing options', () => {
    const path = recommendationPaths.financing(
      { type: 'business', parameters: { initialInvestment: 60000, monthlyCost: 4000 }, timeline: 2 },
      { savingsGap: 50000, monthlyToSave: 2000 },
      baseProfile,
    );

    expect(path?.options?.length).toBe(2);
    expect(path?.options?.[1]?.name).toContain('Investor');
  });
});

describe('combined path', () => {
  it('combines multiple strategies as the recommended path', () => {
    const goal = { type: 'home_purchase', parameters: { homePrice: 400000 }, timeline: 5 };
    const path = recommendationPaths.combined(baseProfile, goal, baseGap);

    expect(path?.pathId).toBe('combined');
    expect(path?.title).toContain('RECOMMENDED');
    expect(path?.mostRealistic).toBe(true);
    expect(path?.combinedPaths).toEqual(
      expect.arrayContaining(['career_advancement', 'side_income', 'expense_reduction']),
    );
    expect(path?.monthlyBoost).toBeGreaterThan(0);
    expect(path?.projections).toHaveLength(5);
    expect(path?.projections[4]?.cumulativeSavings).toBeGreaterThan(path?.projections[0]?.cumulativeSavings ?? 0);
  });

  it('works across different goal types', () => {
    const goals = [
      { type: 'car_purchase', parameters: { carPrice: 28000 }, timeline: 2 },
      { type: 'apartment_move', parameters: { monthlyRent: 1800, movingCosts: 1000 }, timeline: 1 },
      { type: 'baby', parameters: { preparationCost: 9000 }, timeline: 1.5 },
    ];

    goals.forEach((goal) => {
      const path = recommendationPaths.combined(baseProfile, goal, {
        savingsGap: 15000,
        incomeGap: 12000,
        monthlyToSave: 800,
      });
      expect(path?.monthlyBoost).toBeGreaterThan(0);
      expect(path?.projections).toHaveLength(5);
    });
  });
});

describe('invalid inputs', () => {
  it('returns null for invalid path inputs', () => {
    expect(recommendationPaths.careerAdvancement(null, null, null)).toBeNull();
    expect(recommendationPaths.financing(null, null, null)).toBeNull();
    expect(recommendationPaths.timelineExtension({ type: 'baby', timeline: 0 }, baseGap)).toBeNull();
  });
});
