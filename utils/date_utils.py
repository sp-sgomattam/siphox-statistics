from datetime import datetime, timedelta
import numpy as np

major_american_holidays = [
    "2024-01-01",  # New Year's Day
    "2024-01-15",  # Martin Luther King Jr. Day
    "2024-02-19",  # Presidents' Day
    "2024-05-27",  # Memorial Day
    "2024-07-04",  # Independence Day
    "2024-09-02",  # Labor Day
    "2024-10-14",  # Columbus Day
    "2024-11-11",  # Veterans Day
    "2024-11-28",  # Thanksgiving Day
    "2024-12-25",  # Christmas Day
]

# convert dates to est
def convert_to_est(date, is_dst):
    hours_to_subtract = 4 if is_dst else 5
    return date - timedelta(hours=hours_to_subtract)

# function that returns the updated date
def date_updated(start_date, days_to_add):
    time_change = timedelta(days=days_to_add)
    new_date = start_date + time_change
    return new_date  

# function that takes the updated date and calculates days since then
def calc_diff_days(start_date, days_to_add, holidays=major_american_holidays):
    # Ensure start_date is a datetime object
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")
    
    new_date = date_updated(start_date, days_to_add)  # Calculate new date
    today = datetime.now()  # Use current date and time

    # Ensure holidays are in datetime.date format
    holidays = [datetime.strptime(day, "%Y-%m-%d").date() if isinstance(day, str) else day for day in holidays]
    
    # Calculate the number of full business days
    full_business_days = np.busday_count(new_date.date(), today.date(), holidays=holidays)
    
    # Calculate fractional part of the day for new_date and today
    if today.date() > new_date.date() and np.is_busday(new_date.date(), holidays=holidays):
        start_fraction = (new_date + timedelta(days=1) - new_date).total_seconds() / (24 * 3600)
    else:
        start_fraction = 0
    
    if np.is_busday(today.date(), holidays=holidays):
        end_fraction = today.hour / 24 + today.minute / 1440 + today.second / 86400 + today.microsecond / 86400000000
    else:
        end_fraction = 0

    total_days_fractional = full_business_days + end_fraction - start_fraction
    
    return round(total_days_fractional, 3)

# function that takes the updated date and calculates days since then
def calc_diff_days2(start_date, end_date, holidays=major_american_holidays):
    # Ensure start_date is a datetime object
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")

    # Ensure end_date is a datetime object
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S.%f")
    
    # Ensure holidays are in datetime.date format
    holidays = [datetime.strptime(day, "%Y-%m-%d").date() if isinstance(day, str) else day for day in holidays]
    
    # Calculate the number of full business days
    full_business_days = np.busday_count(start_date.date(), end_date.date(), holidays=holidays)
    
    # Calculate fractional part of the day for new_date and today
    if end_date.date() > start_date.date() and np.is_busday(start_date.date(), holidays=holidays):
        start_fraction = (start_date + timedelta(days=1) - start_date).total_seconds() / (24 * 3600)
    else:
        start_fraction = 0
    
    if np.is_busday(end_date.date(), holidays=holidays):
        end_fraction = end_date.hour / 24 + end_date.minute / 1440 + end_date.second / 86400 + end_date.microsecond / 86400000000
    else:
        end_fraction = 0

    total_days_fractional = full_business_days + end_fraction - start_fraction
    
    return round(total_days_fractional, 3)