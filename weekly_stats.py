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
    colin_data = df[(df["sampleDelivered"] == True) | (df["sampleReceived"] == True)]
    colin_data = colin_data[colin_data["sampleResulted"] == True]
    colin_data = colin_data[
        [
            "sampleID",
            "sampleReceived",
            "sampleResulted",
            "sampleReceivedDiff",
            "sampleResultedDiff",
            "createdDate",
        ]
    ]

    colin_data["receivedDate"] = colin_data.apply(
        lambda x: (
            date_updated(x["createdDate"], x["sampleReceivedDiff"])
            if not pd.isna(x["sampleReceivedDiff"])
            else None
        ),
        axis=1,
    )
    colin_data["resultedDate"] = colin_data.apply(
        lambda x: (
            date_updated(x["createdDate"], x["sampleResultedDiff"])
            if not pd.isna(x["sampleResultedDiff"])
            else None
        ),
        axis=1,
    )
    colin_data["processingTime"] = colin_data.apply(calc_processing_time, axis=1)
    colin_data.to_csv("raw_data.csv")

    colin_data["resultedDate"] = pd.to_datetime(colin_data["resultedDate"])

    # Convert processingTime to numeric
    colin_data["processingTime"] = pd.to_numeric(
        colin_data["processingTime"], errors="coerce"
    )

    monthly_data = {}
    for month in months:
        month_data = colin_data[
            (colin_data["resultedDate"].dt.month == month)
            & (colin_data["resultedDate"].dt.year == year)
        ]
        under_two = month_data[month_data["processingTime"] <= 2]
        two_to_four = month_data[
            (month_data["processingTime"] > 2) & (month_data["processingTime"] <= 4)
        ]
        more_than_four = month_data[month_data["processingTime"] > 4]
        total = month_data["processingTime"].count()

        monthly_data[month] = {
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

    months_to_process = [1, 2, 3, 4, 5, 6, 7]
    summary_data = process_data_for_months(df, 2024, months_to_process)

    # Save to CSV
    summary_data.to_csv("monthly_processing_time_summary.csv")

# executes main when running locally
if __name__ == "__main__":
    data = main()