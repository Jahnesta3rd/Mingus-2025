from generate_schedule import generate_schedule

dates = generate_schedule("2025-06-01", "bi-weekly")
print("Forecasted Dates:")
for d in dates:
    print(d)
