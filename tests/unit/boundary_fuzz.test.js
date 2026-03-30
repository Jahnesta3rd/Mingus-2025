const {
  ref_annual_fuel_cost,
  ref_cost_per_mile,
  ref_pmt,
  ref_front_end_dti,
  ref_back_end_dti,
  ref_cap_rate,
  ref_cash_on_cash,
} = require('../validation/reference_calcs');

const {
  calculateCapRate,
  calculateRoi,
} = require('./investment_property_calculations');

// Local copy of business mileage deduction logic to avoid importing test internals.
const IRS_MILEAGE_RATE_2024 = 0.67;
function businessMileageDeduction({ annual_miles, business_pct }) {
  if (business_pct < 0 || business_pct > 1) {
    throw new Error('Invalid business_pct for mileage deduction');
  }
  return Math.round((annual_miles * business_pct * IRS_MILEAGE_RATE_2024 + Number.EPSILON) * 100) / 100;
}

describe('Boundary tests – vehicle', () => {
  it('annual_miles = 0 yields cost_per_mile 0 (not NaN/Infinity)', () => {
    const cpm = ref_cost_per_mile(0, 30, 3.5, 400, 100, 50);
    expect(Number.isFinite(cpm)).toBe(true);
    expect(cpm).toBe(0);
  });

  it('gas_price = 0 yields fuel cost 0 and no crash', () => {
    const fuel = ref_annual_fuel_cost(12000, 30, 0);
    expect(fuel).toBe(0);
  });

  it('mpg = 0 throws a clear error', () => {
    expect(() => ref_annual_fuel_cost(12000, 0, 3.5)).toThrow(/mpg/i);
  });

  it('annual_miles = 500000 yields finite cost_per_mile', () => {
    const cpm = ref_cost_per_mile(500000, 30, 3.5, 400, 100, 50);
    expect(Number.isFinite(cpm)).toBe(true);
  });

  it('business_pct = 1.0 yields deduction = miles * IRS rate', () => {
    const annual_miles = 18000;
    const deduction = businessMileageDeduction({ annual_miles, business_pct: 1.0 });
    expect(deduction).toBeCloseTo(annual_miles * 0.67, 2);
  });

  it('business_pct = 1.5 is rejected with clear error', () => {
    expect(() => businessMileageDeduction({ annual_miles: 18000, business_pct: 1.5 })).toThrow(
      /business_pct/i
    );
  });
});

describe('Boundary tests – housing / mortgage', () => {
  it('rate = 0 => PMT = principal / n, no division error', () => {
    const principal = 200000;
    const termYears = 30;
    const pmtZeroRate = ref_pmt(principal, 0, termYears);
    expect(pmtZeroRate).toBeCloseTo(principal / (termYears * 12), 2);
    expect(Number.isFinite(pmtZeroRate)).toBe(true);
  });

  it('rate = 0.30 produces finite payment', () => {
    const pmtHighRate = ref_pmt(200000, 0.30, 30);
    expect(Number.isFinite(pmtHighRate)).toBe(true);
    expect(pmtHighRate).toBeGreaterThan(0);
  });

  it('term_years = 1 and 50 both yield finite PMT', () => {
    const pmt1 = ref_pmt(200000, 0.065, 1);
    const pmt50 = ref_pmt(200000, 0.065, 50);
    expect(Number.isFinite(pmt1)).toBe(true);
    expect(Number.isFinite(pmt50)).toBe(true);
  });

  it('principal = 0 => PMT throws invalid principal error', () => {
    expect(() => ref_pmt(0, 0.05, 30)).toThrow(/principal/i);
  });

  it('down_payment > purchase_price => negative principal is rejected', () => {
    const purchase = 300000;
    const down = 350000;
    const principal = purchase - down;
    expect(principal).toBeLessThan(0);
    expect(() => ref_pmt(principal, 0.05, 30)).toThrow(/principal/i);
  });

  it('income = 0 => DTI functions do not divide by zero and return finite', () => {
    const pmt = 1500;
    const front = ref_front_end_dti(pmt, 300, 100, 0);
    const back = ref_back_end_dti(pmt, 300, 100, 400, 0);
    expect(Number.isFinite(front)).toBe(true);
    expect(Number.isFinite(back)).toBe(true);
  });
});

describe('Boundary tests – investment property', () => {
  it('property_value = 0 => cap rate throws clear error', () => {
    expect(() => ref_cap_rate(10000, 0)).toThrow(/property value/i);
    expect(() => calculateCapRate({ netMonthlyIncome: 1000, propertyValue: 0 })).toThrow(
      /property value/i
    );
  });

  it('rental_income = 0 => finite (possibly negative) cap rate based on NOI', () => {
    const noiAnnual = -12000;
    const cap = ref_cap_rate(noiAnnual, 300000);
    expect(Number.isFinite(cap)).toBe(true);
  });

  it('cash_invested = 0 => cash-on-cash throws clear error', () => {
    expect(() => ref_cash_on_cash(10000, 0)).toThrow(/cash invested/i);
    expect(() => calculateRoi({ annualCashFlow: 10000, cashInvested: 0 })).toThrow(/cash invested/i);
  });
});

describe('Fuzz invariants', () => {
  function randomIn(min, max) {
    return min + Math.random() * (max - min);
  }

  it('Vehicle invariant: increasing annual_miles never reduces total_annual_cost', () => {
    for (let i = 0; i < 20; i++) {
      const mpg = randomIn(10, 60);
      const gas = randomIn(2.5, 6.0);
      const payment = randomIn(0, 800);
      const insurance = randomIn(50, 300);

      const miles1 = randomIn(1000, 20000);
      const miles2 = randomIn(miles1, 50000);

      const cost1 =
        ref_annual_fuel_cost(miles1, mpg, gas) +
        payment * 12 +
        insurance * 12;
      const cost2 =
        ref_annual_fuel_cost(miles2, mpg, gas) +
        payment * 12 +
        insurance * 12;

      expect(cost2).toBeGreaterThanOrEqual(cost1 - 1e-6);
    }
  });

  it('Housing invariant: increasing interest_rate never reduces monthly_payment', () => {
    for (let i = 0; i < 20; i++) {
      const principal = randomIn(50000, 1500000);
      const rate1 = randomIn(0.02, 0.10);
      const rate2 = randomIn(rate1, 0.15);
      const term = randomIn(5, 30);

      const pmt1 = ref_pmt(principal, rate1, term);
      const pmt2 = ref_pmt(principal, rate2, term);

      expect(pmt2).toBeGreaterThanOrEqual(pmt1 - 1e-6);
    }
  });

  it('Investment invariant: increasing property_value (NOI fixed) never increases cap_rate', () => {
    for (let i = 0; i < 20; i++) {
      const noi = randomIn(0, 200000);
      const v1 = randomIn(100000, 2000000);
      const v2 = randomIn(v1, 5000000);

      const cap1 = ref_cap_rate(noi, v1);
      const cap2 = ref_cap_rate(noi, v2);

      expect(cap2).toBeLessThanOrEqual(cap1 + 1e-6);
    }
  });
});

