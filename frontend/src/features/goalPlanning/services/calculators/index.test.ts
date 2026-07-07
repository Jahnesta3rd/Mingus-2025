import {
  costCalculator,
  expenseIncreaseCalculator,
  gapCalculator,
  incomeNeededCalculator,
  projectSavingsOverTime,
} from './index';

describe('costCalculator', () => {
  it('calculates home purchase with closing costs', () => {
    const result = costCalculator({ type: 'home_purchase', homePrice: 400000 });
    expect(result).toEqual({
      totalCost: 420000,
      breakdown: { homePrice: 400000, closingCosts: 20000 },
    });
  });

  it('calculates car purchase with taxes and fees', () => {
    const result = costCalculator({ type: 'car_purchase', carPrice: 30000 });
    expect(result).toEqual({
      totalCost: 33000,
      breakdown: { carPrice: 30000, taxesAndFees: 3000 },
    });
  });

  it('calculates apartment move with deposit and moving costs', () => {
    const result = costCalculator({
      type: 'apartment_move',
      monthlyRent: 2000,
      movingCosts: 1500,
    });
    expect(result).toEqual({
      totalCost: 7500,
      breakdown: { deposit: 6000, movingCosts: 1500 },
    });
  });

  it('calculates baby preparation cost', () => {
    const result = costCalculator({ type: 'baby', preparationCost: 8000 });
    expect(result).toEqual({
      totalCost: 8000,
      breakdown: { preparationCost: 8000 },
    });
  });

  it('calculates business startup with six-month runway', () => {
    const result = costCalculator({
      type: 'business',
      initialInvestment: 50000,
      monthlyCost: 4000,
    });
    expect(result).toEqual({
      totalCost: 74000,
      breakdown: { initialInvestment: 50000, runway: 24000 },
    });
  });

  it('returns null for invalid or unknown goal types', () => {
    expect(costCalculator(null)).toBeNull();
    expect(costCalculator({ type: 'home_purchase' })).toBeNull();
    expect(costCalculator({ type: 'unknown_goal', homePrice: 100000 })).toBeNull();
  });
});

describe('gapCalculator', () => {
  const homeGoal = { type: 'home_purchase' as const, homePrice: 400000 };

  it('handles zero savings', () => {
    const result = gapCalculator(homeGoal, { savings: 0, income: 10000 }, 5);
    expect(result).toMatchObject({
      totalNeeded: 420000,
      haveNow: 0,
      gap: 420000,
      monthlyToSave: 7000,
      yearlyToSave: 84000,
      feasible: false,
    });
  });

  it('handles negative gap when savings exceed goal cost', () => {
    const result = gapCalculator(homeGoal, { savings: 500000, income: 10000 }, 5);
    expect(result).toMatchObject({
      totalNeeded: 420000,
      haveNow: 500000,
      gap: -80000,
      monthlyToSave: -1333.3333333333333,
      yearlyToSave: -16000,
      feasible: true,
    });
  });

  it('prefers goal.downPaymentAmount over profile savings', () => {
    const result = gapCalculator(
      { ...homeGoal, downPaymentAmount: 80000 },
      { savings: 20000, income: 10000 },
      4,
    );
    expect(result?.haveNow).toBe(80000);
    expect(result?.gap).toBe(340000);
  });

  it('handles a very short timeline (6 months)', () => {
    const result = gapCalculator(homeGoal, { savings: 0, income: 20000 }, 0.5);
    expect(result?.monthlyToSave).toBe(70000);
    expect(result?.yearlyToSave).toBe(840000);
  });

  it('handles a very long timeline (20 years)', () => {
    const result = gapCalculator(homeGoal, { savings: 20000, income: 8000 }, 20);
    expect(result?.monthlyToSave).toBe(1666.6666666666667);
    expect(result?.feasible).toBe(true);
  });

  it('marks feasibility using monthly income sanity check', () => {
    const feasible = gapCalculator(homeGoal, { savings: 0, income: 20000 }, 10);
    const infeasible = gapCalculator(homeGoal, { savings: 0, income: 2000 }, 10);
    expect(feasible?.feasible).toBe(true);
    expect(infeasible?.feasible).toBe(false);
  });

  it('handles extreme income levels', () => {
    const ultraHigh = gapCalculator(homeGoal, { savings: 0, income: 1_000_000 }, 1);
    const ultraLow = gapCalculator(homeGoal, { savings: 0, income: 100 }, 1);
    expect(ultraHigh?.feasible).toBe(true);
    expect(ultraLow?.feasible).toBe(false);
  });

  it('returns null for invalid timeline or goal', () => {
    expect(gapCalculator(homeGoal, { savings: 0, income: 5000 }, 0)).toBeNull();
    expect(gapCalculator(homeGoal, { savings: 0, income: 5000 }, -2)).toBeNull();
    expect(gapCalculator(null, { savings: 0, income: 5000 }, 5)).toBeNull();
  });
});

describe('incomeNeededCalculator', () => {
  it('applies housing affordability rule for home purchase', () => {
    const result = incomeNeededCalculator('home_purchase', 2800);
    expect(result).toEqual({
      neededMonthly: 10000,
      neededAnnualIncome: 120000,
      insufficientBy: null,
    });
  });

  it('applies car affordability rule', () => {
    const result = incomeNeededCalculator('car_purchase', 600);
    expect(result?.neededMonthly).toBeCloseTo(4000);
    expect(result?.neededAnnualIncome).toBeCloseTo(48000);
  });

  it('applies apartment affordability rule', () => {
    const result = incomeNeededCalculator('apartment_move', 1500);
    expect(result?.neededMonthly).toBe(5000);
  });

  it('applies baby and business income buffers', () => {
    expect(incomeNeededCalculator('baby', 4000)?.neededMonthly).toBe(6000);
    expect(incomeNeededCalculator('business', 5000)?.neededMonthly).toBe(10000);
  });

  it('calculates insufficientBy when current annual income is provided', () => {
    const result = incomeNeededCalculator('home_purchase', 2800, 90000);
    expect(result?.insufficientBy).toBe(30000);
  });

  it('returns null for invalid inputs', () => {
    expect(incomeNeededCalculator('home_purchase', -100)).toBeNull();
    expect(incomeNeededCalculator('unknown_goal', 2000)).toBeNull();
    expect(incomeNeededCalculator(null, 2000)).toBeNull();
  });
});

describe('expenseIncreaseCalculator', () => {
  const currentAnnualExpenses = 48000;

  it('estimates home ownership expense increase', () => {
    const result = expenseIncreaseCalculator(
      { type: 'home_purchase', homePrice: 400000 },
      currentAnnualExpenses,
    );
    expect(result).toEqual({
      currentMonthly: 4000,
      newMonthly: 4166.666666666667,
      monthlyIncrease: 166.66666666666666,
      annualIncrease: 2000,
    });
  });

  it('estimates car ownership expense increase', () => {
    const result = expenseIncreaseCalculator(
      { type: 'car_purchase', carPrice: 30000 },
      currentAnnualExpenses,
    );
    expect(result?.annualIncrease).toBe(2400);
    expect(result?.monthlyIncrease).toBe(200);
  });

  it('treats apartment move as full annual rent increase', () => {
    const result = expenseIncreaseCalculator(
      { type: 'apartment_move', monthlyRent: 1800 },
      currentAnnualExpenses,
    );
    expect(result?.annualIncrease).toBe(21600);
    expect(result?.newMonthly).toBe(5800);
  });

  it('adds baby annual costs and zero for sabbatical', () => {
    expect(
      expenseIncreaseCalculator({ type: 'baby' }, currentAnnualExpenses)?.annualIncrease,
    ).toBe(15000);
    expect(
      expenseIncreaseCalculator({ type: 'sabbatical' }, currentAnnualExpenses)?.annualIncrease,
    ).toBe(0);
  });

  it('returns null for invalid inputs', () => {
    expect(expenseIncreaseCalculator(null, currentAnnualExpenses)).toBeNull();
    expect(expenseIncreaseCalculator({ type: 'baby' }, -1)).toBeNull();
    expect(expenseIncreaseCalculator({ type: 'home_purchase' }, currentAnnualExpenses)).toBeNull();
  });
});

describe('projectSavingsOverTime', () => {
  const homeGoal = { type: 'home_purchase' as const, homePrice: 120000 };

  it('projects cumulative savings toward goal', () => {
    const projection = projectSavingsOverTime(
      { savings: 10000, income: 8000 },
      homeGoal,
      3,
      2000,
    );
    expect(projection).toHaveLength(3);
    expect(projection[0]).toEqual({ year: 1, cumulativeSavings: 34000, goalReached: false });
    expect(projection[2]).toEqual({ year: 3, cumulativeSavings: 82000, goalReached: false });
  });

  it('marks goalReached when cumulative savings meet total cost', () => {
    const projection = projectSavingsOverTime(
      { savings: 50000 },
      homeGoal,
      2,
      5000,
    );
    expect(projection[1]?.goalReached).toBe(true);
    expect(projection[1]?.cumulativeSavings).toBe(170000);
  });

  it('handles negative gap by reaching goal immediately in projection', () => {
    const projection = projectSavingsOverTime(
      { savings: 200000 },
      homeGoal,
      1,
      0,
    );
    expect(projection[0]?.goalReached).toBe(true);
  });

  it('supports fractional timelines (6 months)', () => {
    const projection = projectSavingsOverTime(
      { savings: 0 },
      homeGoal,
      0.5,
      1000,
    );
    expect(projection).toHaveLength(1);
    expect(projection[0]?.cumulativeSavings).toBe(6000);
  });

  it('supports long timelines (20 years)', () => {
    const projection = projectSavingsOverTime(
      { savings: 0 },
      { type: 'baby', preparationCost: 10000 },
      20,
      50,
    );
    expect(projection).toHaveLength(20);
    expect(projection[19]?.cumulativeSavings).toBe(12000);
    expect(projection[19]?.goalReached).toBe(true);
  });

  it('returns empty array for invalid inputs', () => {
    expect(projectSavingsOverTime({ savings: 0 }, homeGoal, 0, 100)).toEqual([]);
    expect(projectSavingsOverTime({ savings: 0 }, null, 5, 100)).toEqual([]);
    expect(projectSavingsOverTime({ savings: 0 }, homeGoal, 5, NaN)).toEqual([]);
  });
});
