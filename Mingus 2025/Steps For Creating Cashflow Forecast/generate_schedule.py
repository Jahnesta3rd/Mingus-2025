from datetime import datetime, timedelta
from dateutil.rrule import rrule, WEEKLY, MONTHLY, YEARLY

def generate_schedule(start_date_str, frequency):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = start_date + timedelta(days=30)

    freq_map = {
        'weekly': rrule(WEEKLY, dtstart=start_date, until=end_date),
        'bi-weekly': rrule(WEEKLY, interval=2, dtstart=start_date, until=end_date),
        'monthly': rrule(MONTHLY, dtstart=start_date, until=end_date),
        'quarterly': rrule(MONTHLY, interval=3, dtstart=start_date, until=end_date),
        'annually': rrule(YEARLY, dtstart=start_date, until=end_date)
    }

    return [dt.strftime("%Y-%m-%d") for dt in freq_map[frequency]]