// Independent reference implementations for Mingus financial calculations.
// NOTE: This file MUST NOT import anything from the main application.

// ─────────────────────────────────────────────────────────────────────────────
// Vehicle
// ─────────────────────────────────────────────────────────────────────────────

function ref_annual_fuel_cost(miles, mpg, gas_price) {
  if (mpg === 0) {
    throw new Error('Invalid mpg: cannot be zero');
  }
  if (!mpg || mpg < 0) {
    throw new Error('Invalid mpg');
  }
  return (miles / mpg) * gas_price;
}

function ref_cost_per_mile(miles, mpg, gas_price, payment, insurance, maint) {
  // Zero or negative miles means no distance to spread costs across.
  if (!miles || miles <= 0) return 0;
  const fuel = ref_annual_fuel_cost(miles, mpg, gas_price);
  const totalAnnual =
    fuel +
    (payment || 0) * 12 +
    (insurance || 0) * 12 +
    (maint || 0) * 12;
  return totalAnnual / miles;
}

function ref_irs_deduction(business_miles, rate = 0.67) {
  return business_miles * rate;
}

function ref_vehicle_roi(purchase_price, current_value) {
  if (!purchase_price || purchase_price <= 0) {
    throw new Error('Invalid purchase price for vehicle ROI');
  }
  return ((current_value - purchase_price) / purchase_price) * 100;
}

// ─────────────────────────────────────────────────────────────────────────────
// Housing
// ─────────────────────────────────────────────────────────────────────────────

function ref_pmt(principal, annual_rate, term_years) {
  if (!principal || principal < 0) {
    throw new Error('Invalid principal for PMT');
  }
  if (!term_years || term_years <= 0) {
    throw new Error('Invalid term for PMT');
  }
  const n = term_years * 12;
  // 0% mortgage: simple amortization
  if (!annual_rate || annual_rate === 0) {
    return principal / n;
  }
  const r = annual_rate / 12;
  const factor = Math.pow(1 + r, n);
  return (principal * (r * factor)) / (factor - 1);
}

function ref_front_end_dti(pmt, monthly_tax, insurance, gross_monthly_income) {
  if (!gross_monthly_income) return 0;
  const piti = (pmt || 0) + (monthly_tax || 0) + (insurance || 0);
  return piti / gross_monthly_income;
}

function ref_back_end_dti(pmt, monthly_tax, insurance, other_debt, gross_monthly_income) {
  if (!gross_monthly_income) return 0;
  const piti = (pmt || 0) + (monthly_tax || 0) + (insurance || 0);
  const total = piti + (other_debt || 0);
  return total / gross_monthly_income;
}

function ref_refi_savings(balance, old_rate, new_rate, remaining_term_years) {
  if (!balance || balance <= 0 || !remaining_term_years || remaining_term_years <= 0) {
    throw new Error('Invalid inputs for refi savings');
  }
  const oldPmt = ref_pmt(balance, old_rate, remaining_term_years);
  const newPmt = ref_pmt(balance, new_rate, remaining_term_years);
  return oldPmt - newPmt;
}

function ref_refi_breakeven(closing_costs, monthly_savings) {
  if (!monthly_savings || monthly_savings <= 0) return 0;
  return closing_costs / monthly_savings;
}

// ─────────────────────────────────────────────────────────────────────────────
// Investment property
// ─────────────────────────────────────────────────────────────────────────────

function ref_cap_rate(noi, property_value) {
  if (!property_value || property_value <= 0) {
    throw new Error('Invalid property value for cap rate');
  }
  return (noi / property_value) * 100;
}

function ref_cash_on_cash(annual_cash_flow, cash_invested) {
  if (!cash_invested || cash_invested <= 0) {
    throw new Error('Invalid cash invested for cash-on-cash');
  }
  return (annual_cash_flow / cash_invested) * 100;
}

module.exports = {
  ref_annual_fuel_cost,
  ref_cost_per_mile,
  ref_irs_deduction,
  ref_vehicle_roi,
  ref_pmt,
  ref_front_end_dti,
  ref_back_end_dti,
  ref_refi_savings,
  ref_refi_breakeven,
  ref_cap_rate,
  ref_cash_on_cash,
};

