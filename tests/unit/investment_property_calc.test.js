const {
  DEFAULT_DOWN_PAYMENT_PCT,
  calculateCapRate,
  calculateMonthlyCashFlow,
  calculateRoi,
  estimateCashInvestedFromDownPayment,
} = require('./investment_property_calculations');

describe('Investment property calculations – Dr. Jasmine Williams (Professional tier)', () => {
  const scenario = {
    propertyValue: 520000,
    purchasePrice: 485000,
    estimatedRentalIncome: 2800,
    estimatedExpenses: 1400,
    // Net monthly income from prompt: 2800 - 1400 = 1400
    netMonthlyIncome: 1400,
    // Reported cap rate and ROI from current production data:
    reportedCapRate: 3.2,
    reportedMonthlyCashFlow: -1400,
    reportedRoi: 16.8,
  };

  it('computes cap rate using Cap Rate = (Annual NOI / Property Value) * 100 and matches ~3.2%', () => {
    const capRate = calculateCapRate({
      netMonthlyIncome: scenario.netMonthlyIncome,
      propertyValue: scenario.propertyValue,
    });

    // Annual NOI = 1,400 * 12 = 16,800
    // Cap Rate = (16,800 / 520,000) * 100 ≈ 3.23%
    expect(capRate).toBeCloseTo(3.23, 2);
    expect(capRate).toBeCloseTo(scenario.reportedCapRate, 1);
  });

  it('derives the mortgage payment from the reported negative cash flow and keeps sign consistent', () => {
    // Cash Flow = Net Monthly Income - Monthly Mortgage Payment
    // -1,400 = 1,400 - M  =>  M = 2,800
    const impliedMortgagePayment =
      scenario.netMonthlyIncome - scenario.reportedMonthlyCashFlow;

    expect(impliedMortgagePayment).toBe(2800);

    const computedCashFlow = calculateMonthlyCashFlow({
      netMonthlyIncome: scenario.netMonthlyIncome,
      monthlyMortgagePayment: impliedMortgagePayment,
    });

    expect(computedCashFlow).toBeLessThan(0);
    expect(computedCashFlow).toBe(scenario.reportedMonthlyCashFlow);
  });

  it('flags that a positive 16.8% ROI is inconsistent with a negative annual cash flow', () => {
    const impliedMortgagePayment =
      scenario.netMonthlyIncome - scenario.reportedMonthlyCashFlow; // 2,800
    const annualCashFlow =
      calculateMonthlyCashFlow({
        netMonthlyIncome: scenario.netMonthlyIncome,
        monthlyMortgagePayment: impliedMortgagePayment,
      }) * 12; // -16,800

    expect(annualCashFlow).toBeLessThan(0);

    const cashInvested = estimateCashInvestedFromDownPayment(
      scenario.purchasePrice,
      DEFAULT_DOWN_PAYMENT_PCT
    );

    const roi = calculateRoi({ annualCashFlow, cashInvested });

    // With a conventional 20% down-payment assumption, ROI must be negative.
    expect(roi).toBeLessThan(0);

    // If we force ROI to be +16.8% with the same negative cash flow, we
    // would need a negative cash invested amount, which is impossible.
    const impliedCashInvestedForReportedRoi =
      annualCashFlow / (scenario.reportedRoi / 100);
    expect(impliedCashInvestedForReportedRoi).toBeLessThan(0);
  });
});

