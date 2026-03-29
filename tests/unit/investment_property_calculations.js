// Canonical investment property calculation helpers for Mingus.
// These mirror the formulas used in the Python housing tests and make
// assumptions explicit for ROI.

// Assumed down payment percentage when cash invested is not provided explicitly.
// This constant should be surfaced in any UI tooltip/footnote that explains ROI.
const DEFAULT_DOWN_PAYMENT_PCT = 0.20;

/**
 * Cap Rate = (Annual NOI / Property Value) * 100
 */
function calculateCapRate({ netMonthlyIncome, propertyValue }) {
  if (!propertyValue || propertyValue <= 0) {
    throw new Error('Invalid property value for cap rate');
  }
  if (typeof netMonthlyIncome !== 'number') {
    throw new Error('Invalid netMonthlyIncome');
  }
  const annualNoi = netMonthlyIncome * 12;
  return (annualNoi / propertyValue) * 100;
}

/**
 * Cash Flow = Net Monthly Income - Monthly Mortgage Payment
 */
function calculateMonthlyCashFlow({ netMonthlyIncome, monthlyMortgagePayment }) {
  if (typeof netMonthlyIncome !== 'number' || typeof monthlyMortgagePayment !== 'number') {
    return 0;
  }
  return netMonthlyIncome - monthlyMortgagePayment;
}

/**
 * Cash-on-Cash / ROI = (Annual Cash Flow / Cash Invested) * 100
 */
function calculateRoi({ annualCashFlow, cashInvested }) {
  if (!cashInvested || cashInvested <= 0) {
    throw new Error('Invalid cash invested for ROI');
  }
  return (annualCashFlow / cashInvested) * 100;
}

function estimateCashInvestedFromDownPayment(purchasePrice, downPaymentPct = DEFAULT_DOWN_PAYMENT_PCT) {
  if (!purchasePrice) return 0;
  return purchasePrice * downPaymentPct;
}

module.exports = {
  DEFAULT_DOWN_PAYMENT_PCT,
  calculateCapRate,
  calculateMonthlyCashFlow,
  calculateRoi,
  estimateCashInvestedFromDownPayment,
};

