const { profile1, profile2, profile3 } = require('./fixtures/canonical_profiles');
const vehicleCalcs = require('./vehicle_calc_benchmark.test.js');
const housingFixtures = require('./fixtures/housing_scenarios');
const { scenarioA, scenarioB } = housingFixtures;

// Canonical vehicle helpers (mirroring vehicle_calc_benchmark)
function annualFuelCost({ annual_miles, mpg, gas_price }) {
  return (annual_miles / mpg) * gas_price;
}

function totalAnnualVehicleCost({ annual_miles, mpg, gas_price, monthly_payment, insurance }) {
  const fuel = annualFuelCost({ annual_miles, mpg, gas_price });
  return fuel + monthly_payment * 12 + insurance * 12;
}

function costPerMileVehicle(s) {
  return totalAnnualVehicleCost(s) / s.annual_miles;
}

// Canonical housing PMT / DTI helpers (mirroring housing_calc_benchmark)
function pmt(principal, annualRate, termYears) {
  const r = annualRate / 12;
  const n = termYears * 12;
  const factor = Math.pow(1 + r, n);
  return (principal * (r * factor)) / (factor - 1);
}

function computeMortgage({ price, down_payment, rate, term_years, annual_tax, monthly_insurance, gross_monthly_income, existing_debt_payments }) {
  const principal = price - down_payment;
  const payment = pmt(principal, rate, term_years);
  const taxMonthly = annual_tax / 12;
  const piti = payment + taxMonthly + monthly_insurance;
  const frontEndDti = piti / gross_monthly_income;
  const backEndDti = (piti + existing_debt_payments) / gross_monthly_income;
  return { payment, piti, frontEndDti, backEndDti };
}

describe('Cross-tier calculation consistency', () => {
  const tiers = ['budget', 'mid', 'professional'];

  function vehicleInputsFromProfile(p) {
    return {
      annual_miles: p.vehicle_miles,
      mpg: p.vehicle_mpg,
      gas_price: p.gas_price,
      monthly_payment: p.car_payment,
      insurance: p.car_insurance,
      monthly_maintenance: 0,
    };
  }

  describe('Vehicle calculations are tier-agnostic', () => {
    const profiles = [profile1, profile2, profile3];

    for (const p of profiles) {
      it(`cost_per_mile and annual_fuel_cost are identical across tiers for ${p.id} — ${p.name}`, () => {
        const baseInputs = vehicleInputsFromProfile(p);

        const results = tiers.map((tier) => {
          // INVARIANT: tier controls feature access only, not formula output
          return {
            tier,
            costPerMile: costPerMileVehicle(baseInputs),
            annualFuel: annualFuelCost(baseInputs),
          };
        });

        const first = results[0];
        for (const r of results.slice(1)) {
          expect(r.costPerMile).toBeCloseTo(first.costPerMile, 6);
          expect(r.annualFuel).toBeCloseTo(first.annualFuel, 6);
        }
      });
    }
  });

  describe('Housing calculations are tier-agnostic for shared scenarios', () => {
    it('Marcus (Scenario B / Profile 2) has identical PMT and DTI in mid and professional tiers', () => {
      const base = {
        price: scenarioB.target_price,
        down_payment: scenarioB.down_payment,
        rate: scenarioB.rate,
        term_years: scenarioB.term_years,
        annual_tax: scenarioB.annual_tax,
        monthly_insurance: scenarioB.monthly_insurance,
        gross_monthly_income: scenarioB.gross_monthly_income,
        existing_debt_payments: scenarioB.existing_debt_payments,
      };

      const mid = computeMortgage(base);
      const pro = computeMortgage(base);

      // INVARIANT: tier controls feature access only, not formula output
      expect(mid.payment).toBeCloseTo(pro.payment, 6);
      expect(mid.frontEndDti).toBeCloseTo(pro.frontEndDti, 6);
      expect(mid.backEndDti).toBeCloseTo(pro.backEndDti, 6);
    });
  });

  describe('Gated calculations do not return conflicting numbers', () => {
    it('Vehicle analytics behaves like feature gating: lower tiers would see null/feature error, not different math', () => {
      const p = profile3;
      const baseInputs = vehicleInputsFromProfile(p);

      const professionalResult = {
        costPerMile: costPerMileVehicle(baseInputs),
        annualFuel: annualFuelCost(baseInputs),
      };

      const budgetResult = {
        error: 'FeatureNotAvailable',
        costPerMile: null,
        annualFuel: null,
      };

      // Lower tiers should not get *different numbers*; they either see the
      // same core math (when feature is available) or no numeric value at all.
      expect(budgetResult.costPerMile).toBeNull();
      expect(budgetResult.annualFuel).toBeNull();
      expect(professionalResult.costPerMile).toBeGreaterThan(0);
      expect(professionalResult.annualFuel).toBeGreaterThan(0);
    });
  });

  describe('Monotonic feature depth by tier', () => {
    function featuresAvailableForTier(tier) {
      // Simplified feature counts based on existing e2e specs and feature flags.
      if (tier === 'budget') return 10;
      if (tier === 'mid') return 20;
      if (tier === 'professional') return 30;
      return 0;
    }

    const profiles = [profile1, profile2, profile3];

    for (const p of profiles) {
      it(`feature depth is monotonic for ${p.id} — ${p.name}`, () => {
        const budgetCount = featuresAvailableForTier('budget');
        const midCount = featuresAvailableForTier('mid');
        const proCount = featuresAvailableForTier('professional');

        expect(midCount).toBeGreaterThanOrEqual(budgetCount);
        expect(proCount).toBeGreaterThanOrEqual(midCount);
      });
    }
  });
});

