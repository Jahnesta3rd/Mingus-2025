from forecast_loader import insert_forecast_dates

# Sample call to insert forecasted cashflow events into Supabase
if __name__ == "__main__":
    response = insert_forecast_dates(
        user_id="00000000-0000-0000-0000-000000000001",  # replace with real user_id
        reference_id="00000000-0000-0000-0000-000000000099",  # replace with related income_expense_schedule ID
        name="Sample Paycheck",
        frequency="bi-weekly",
        start_date="2025-06-01",
        amount=1500,
        event_type="income"
    )

    print("Insert response:")
    print(response)
