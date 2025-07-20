# Expense Field Standardization

## Overview

This document outlines the standardization of expense field names across the Mingus application to ensure full compatibility between frontend and backend systems.

## Changes Made

### 1. Field Name Standardization

**Before (camelCase):**
- `startingBalance`
- `rentOrMortgageExpense`
- `autoPaymentExpense`
- `creditCard1Name`

**After (snake_case):**
- `starting_balance`
- `rent_or_mortgage_expense`
- `auto_payment_expense`
- `credit_card1_name`

### 2. Added Missing Categories

The following expense categories were added to the main template to match the dynamic setup:

- **Pet Expenses** (`pet_expense`)
- **Fraternity/Sorority** (`fraternity_sorority_expense`)

### 3. Backend Compatibility

- Updated API endpoints to handle snake_case field names
- Added comprehensive validation and normalization utilities
- Implemented proper error handling and data processing

## Field Mapping Chart

| Category | Field Name (snake_case) | Type | Frequency | Due Date | Monthly Calc |
|----------|------------------------|------|-----------|----------|--------------|
| **Starting Balance** | `starting_balance` | number | - | - | - |
| **Housing** | `rent_or_mortgage_expense` | number | ✓ | ✓ | ✓ |
| **Housing** | `utilities_expense` | number | ✓ | ✓ | ✓ |
| **Transportation** | `auto_payment_expense` | number | ✓ | ✓ | ✓ |
| **Transportation** | `auto_insurance_expense` | number | ✓ | ✓ | ✓ |
| **Transportation** | `auto_gas_expense` | number | ✓ | ✓ | ✓ |
| **Transportation** | `bus_fare_expense` | number | ✓ | ✓ | ✓ |
| **Transportation** | `rideshare_expense` | number | ✓ | ✓ | ✓ |
| **Healthcare** | `health_insurance_expense` | number | ✓ | ✓ | ✓ |
| **Healthcare** | `healthcare_expense` | number | ✓ | ✓ | ✓ |
| **Food** | `grocery_expense` | number | ✓ | ✓ | ✓ |
| **Food** | `restaurant_meals_expense` | number | ✓ | ✓ | ✓ |
| **Personal Care** | `personal_care_expense` | number | ✓ | ✓ | ✓ |
| **Personal Care** | `selfcare_expense` | number | ✓ | ✓ | ✓ |
| **Family** | `daycare_expense` | number | ✓ | ✓ | ✓ |
| **Family** | `child_support_expense` | number | ✓ | ✓ | ✓ |
| **Family** | `cash_to_family_expense` | number | ✓ | ✓ | ✓ |
| **Debt** | `credit_card1_expense` | number | ✓ | ✓ | ✓ |
| **Debt** | `credit_card2_expense` | number | ✓ | ✓ | ✓ |
| **Debt** | `credit_card3_expense` | number | ✓ | ✓ | ✓ |
| **Debt** | `loan_1_expense` | number | ✓ | ✓ | ✓ |
| **Debt** | `loan_2_expense` | number | ✓ | ✓ | ✓ |
| **Debt** | `loan_3_expense` | number | ✓ | ✓ | ✓ |
| **Subscriptions** | `subscriptions_expense` | number | ✓ | ✓ | ✓ |
| **Subscriptions** | `mobile_phone_expense` | number | ✓ | ✓ | ✓ |
| **Entertainment** | `entertainment_expense` | number | ✓ | ✓ | ✓ |
| **Entertainment** | `gift_others_expense` | number | ✓ | ✓ | ✓ |
| **Entertainment** | `career_expense` | number | ✓ | ✓ | ✓ |
| **Other** | `pet_expense` | number | ✓ | ✓ | ✓ |
| **Other** | `fraternity_sorority_expense` | number | ✓ | ✓ | ✓ |
| **Text Fields** | `credit_card1_name` | text | - | - | - |
| **Text Fields** | `credit_card2_name` | text | - | - | - |
| **Text Fields** | `credit_card3_name` | text | - | - | - |
| **Text Fields** | `loan_1_name` | text | - | - | - |
| **Text Fields** | `loan_2_name` | text | - | - | - |
| **Text Fields** | `loan_3_name` | text | - | - | - |

## Category Groupings

### Essential Expenses
- `rent_or_mortgage_expense`
- `utilities_expense`
- `auto_payment_expense`
- `auto_insurance_expense`
- `auto_gas_expense`
- `health_insurance_expense`

### Living Expenses
- `grocery_expense`
- `restaurant_meals_expense`
- `personal_care_expense`
- `daycare_expense`
- `child_support_expense`
- `cash_to_family_expense`

### Debt & Subscriptions
- `credit_card1_expense`
- `credit_card2_expense`
- `credit_card3_expense`
- `loan_1_expense`
- `loan_2_expense`
- `loan_3_expense`
- `subscriptions_expense`
- `mobile_phone_expense`

### Discretionary Expenses
- `entertainment_expense`
- `gift_others_expense`
- `career_expense`
- `pet_expense`
- `fraternity_sorority_expense`
- `selfcare_expense`
- `healthcare_expense`
- `bus_fare_expense`
- `rideshare_expense`

## API Endpoints

### Frontend → Backend Data Flow

1. **Form Submission**: Frontend sends snake_case field names
2. **Validation**: Backend validates field structure and names
3. **Normalization**: Data is normalized to ensure consistency
4. **Calculation**: Monthly amounts are calculated for all expenses
5. **Storage**: Data is stored in Supabase with proper field mapping

### Key Endpoints

- `POST /api/expense-profile` - Save expense profile data
- `POST /api/expenses` - Set expense categories during onboarding

## Utility Functions

### Field Mapping Utilities (`backend/utils/field_mapping.py`)

- `validate_expense_data(data)` - Validate expense data structure
- `normalize_expense_data(data)` - Normalize field names and structure
- `calculate_monthly_totals(data)` - Calculate category and total monthly amounts
- `to_monthly_amount(amount, frequency)` - Convert amounts to monthly equivalent
- `get_frequency_field(field)` - Get corresponding frequency field name
- `get_due_date_field(field)` - Get corresponding due date field name

## Testing

### Test Coverage

- ✅ Field definitions consistency
- ✅ Field mapping functions
- ✅ Monthly calculations
- ✅ Data validation
- ✅ Data normalization
- ✅ Totals calculation
- ✅ Frontend-backend compatibility

### Running Tests

```bash
python tests/test_expense_field_mapping.py
```

## Migration Notes

### For Developers

1. **Frontend**: All field names now use snake_case
2. **Backend**: API endpoints expect and return snake_case field names
3. **Database**: Supabase tables use snake_case column names
4. **Validation**: Comprehensive validation ensures data integrity

### For Database

The `user_expense_items` table should have the following structure:

```sql
CREATE TABLE user_expense_items (
    user_id UUID PRIMARY KEY,
    starting_balance DECIMAL(10,2),
    rent_or_mortgage_expense DECIMAL(10,2),
    rent_or_mortgage_frequency VARCHAR(20),
    rent_or_mortgage_due_date DATE,
    rent_or_mortgage_monthly DECIMAL(10,2),
    -- ... (all other expense fields follow same pattern)
    total_monthly_expenses DECIMAL(10,2),
    essential_expenses_total DECIMAL(10,2),
    living_expenses_total DECIMAL(10,2),
    debt_expenses_total DECIMAL(10,2),
    discretionary_expenses_total DECIMAL(10,2),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Compatibility Matrix

| Component | Before | After | Status |
|-----------|--------|-------|--------|
| Frontend Template | camelCase | snake_case | ✅ Updated |
| Frontend JavaScript | camelCase | snake_case | ✅ Updated |
| Backend API | Mixed | snake_case | ✅ Updated |
| Database Schema | snake_case | snake_case | ✅ Compatible |
| Validation | Basic | Comprehensive | ✅ Enhanced |
| Testing | None | Full Coverage | ✅ Added |

## Benefits

1. **Consistency**: All field names follow the same naming convention
2. **Compatibility**: Frontend and backend are fully compatible
3. **Maintainability**: Clear field mapping and validation
4. **Extensibility**: Easy to add new expense categories
5. **Reliability**: Comprehensive testing ensures data integrity

## Future Considerations

1. **Dynamic Categories**: Consider making expense categories configurable
2. **Internationalization**: Field labels can be localized while keeping field names consistent
3. **Analytics**: Category groupings enable better financial insights
4. **Validation Rules**: Add business logic validation (e.g., expense limits) 