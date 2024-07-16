import pandas as pd
from datetime import datetime, timedelta
import numpy as np

from utils.mongo_utils import connect_mongo, pull_mongo_data
from utils.date_utils import (
    convert_to_est,
    date_updated,
    calc_diff_days,
    calc_diff_days2,
)
from utils.slack_utils import send_slack_message
from utils.zapier_utils import send_email
from daily_stats import set_dates


def calc_processing_time(row, holidays=[]):
    if pd.isna(row["sampleReceivedDiff"]) or pd.isna(row["sampleResultedDiff"]):
        return "cannot compute"

    recieved_date = date_updated(row["createdDate"], row["sampleReceivedDiff"])
    resulted_date = date_updated(row["createdDate"], row["sampleResultedDiff"])

    # Calculate the number of full business days
    full_business_days = np.busday_count(
        recieved_date.date(), resulted_date.date(), holidays=holidays
    )

    # Calculate fractional part of the day for new_date and today
    if resulted_date.date() > recieved_date.date() and np.is_busday(
        recieved_date.date(), holidays=holidays
    ):
        start_fraction = (
            recieved_date + timedelta(days=1) - recieved_date
        ).total_seconds() / (24 * 3600)
    else:
        start_fraction = 0

    if np.is_busday(resulted_date.date(), holidays=holidays):
        end_fraction = (
            resulted_date.hour / 24
            + resulted_date.minute / 1440
            + resulted_date.second / 86400
            + resulted_date.microsecond / 86400000000
        )
    else:
        end_fraction = 0

    total_days_fractional = full_business_days + end_fraction - start_fraction
    return round(total_days_fractional, 3)


def process_data_for_months(df, year, months):
    mutated_data = df[(df["sampleDelivered"] == True) | (df["sampleReceived"] == True)]
    mutated_data = mutated_data[mutated_data["sampleResulted"] == True]
    mutated_data = mutated_data[
        [
            "sampleID",
            "sampleReceived",
            "sampleResulted",
            "sampleReceivedDiff",
            "sampleResultedDiff",
            "createdDate",
        ]
    ]

    mutated_data["receivedDate"] = mutated_data.apply(
        lambda x: (
            date_updated(x["createdDate"], x["sampleReceivedDiff"])
            if not pd.isna(x["sampleReceivedDiff"])
            else None
        ),
        axis=1,
    )
    mutated_data["resultedDate"] = mutated_data.apply(
        lambda x: (
            date_updated(x["createdDate"], x["sampleResultedDiff"])
            if not pd.isna(x["sampleResultedDiff"])
            else None
        ),
        axis=1,
    )
    mutated_data["processingTime"] = mutated_data.apply(calc_processing_time, axis=1)

    mutated_data["resultedDate"] = pd.to_datetime(mutated_data["resultedDate"])

    # Convert processingTime to numeric
    mutated_data["processingTime"] = pd.to_numeric(
        mutated_data["processingTime"], errors="coerce"
    )

    monthly_data = {}
    for month in months:
        month_data = mutated_data[
            (mutated_data["resultedDate"].dt.month == month)
            & (mutated_data["resultedDate"].dt.year == year)
        ]
        under_two = month_data[month_data["processingTime"] <= 2]
        two_to_four = month_data[
            (month_data["processingTime"] > 2) & (month_data["processingTime"] <= 4)
        ]
        more_than_four = month_data[month_data["processingTime"] > 4]
        total = month_data["processingTime"].count()

        monthly_data[month] = {
            "Month": month,
            "Under Two": under_two.shape[0],
            "Two to Four": two_to_four.shape[0],
            "More than Four": more_than_four.shape[0],
            "Total": total,
        }
        

    return pd.DataFrame(monthly_data).transpose()


# manages and runs functions
def main():
    # connect and pull data
    client = connect_mongo()
    docs = pull_mongo_data(client)
    df = pd.DataFrame(docs)

    # filter and mutate data
    df = set_dates(df)
    # Specify the months you want to include

    current_month = datetime.now().month
    months_to_process = [current_month]
    summary_data = process_data_for_months(df, 2024, months_to_process)
    all_months = list(range(1, current_month + 1))
    all_data = process_data_for_months(df, 2024, all_months)
    
    messages = []
    for index, row in summary_data.iterrows():
        message = (
            f"For month {row['Month']}, the kit processing results are:\n"
            f"Under Two: {row['Under Two']} [{(row['Under Two'] / row['Total'] * 100).round(2)}%]\n"
            f"Two to Four: {row['Two to Four']} [{(row['Two to Four'] / row['Total'] * 100).round(2)}%]\n"
            f"More than Four: {row['More than Four']} [{(row['More than Four'] / row['Total'] * 100).round(2)}%]\n"
            f"Total: {row['Total']}\n"
        )
        messages.append(message)

    # Combine all messages into one string with the current date
    current_date = datetime.today().strftime("%Y-%m-%d")
    final_message = f"--- KITS RESULTED STATISTICS UP TO {current_date} ---\n\n" + "\n".join(messages) + "\n\nPlease see all data in CSV Below"
    
    summary_path = "monthly_processing_time_summary.csv"
    all_data.to_csv(summary_path, index = False)

    send_slack_message(final_message, summary_path)

# executes main when running locally
if __name__ == "__main__":
    data = main()