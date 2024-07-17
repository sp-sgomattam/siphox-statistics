import pandas as pd
from datetime import datetime, timedelta

from utils.mongo_utils import connect_mongo, pull_mongo_data
from utils.date_utils import (
    convert_to_est,
    date_updated,
    calc_diff_days,
)
from utils.slack_utils import send_slack_message
from utils.zapier_utils import send_email


# set datetime objects and dates to est
def set_dates(df):
    df["lastUpdatedDate"] = pd.to_datetime(df["lastUpdatedDate"])
    df["createdDate"] = pd.to_datetime(df["createdDate"])

    df["lastUpdatedDate"] = df["lastUpdatedDate"].apply(
        lambda x: convert_to_est(x, is_dst=True)
    )
    df["createdDate"] = df["createdDate"].apply(
        lambda x: convert_to_est(x, is_dst=True)
    )

    return df


# filter values based on criteria
def filter_vals(df):
    data = df[(df["sampleDelivered"] == True) | (df["sampleReceived"] == True)]
    data = data[
        (data["sampleCollectionException"] == False)
        & (data["sampleDeliveryException"] == False)
        & (data["sampleCanceled"] == False)
        & (data["kitCanceled"] == False)
        & (data["sampleResulted"] == False)
        & (data["sampleRejected"] == False)
    ]

    # add received on time column and sort by last updated date
    data["collectionRecorded"] = data["sampleCollectedDiff"].notna()
    data["receivedOnTime"] = (
        data["sampleReceivedDiff"] - data["kitRegisteredDiff"] <= 14
    )

    return data


# sanity check to ensure statistics are in order
def statistics_sanity_check(data):
    kit_registered = data["kitRegisteredDiff"].notna()
    sample_collected = data["sampleCollectedDiff"].notna()
    registered_before_coll = data["kitRegisteredDiff"] <= data["sampleCollectedDiff"]
    received_on_time = data["sampleReceivedDiff"] - data["kitRegisteredDiff"] <= 14

    statistics = f"""Total number: {data['kitCanceled'].count()}
    Registered: {data[kit_registered]['kitCanceled'].count()}
    Not Registered: {data[~kit_registered]['kitCanceled'].count()}
    Collection Recorded: {data[sample_collected]['kitCanceled'].count()}
    Collection Not Recorded: {data[~sample_collected]['kitCanceled'].count()}
    Registered before Collection: {data[registered_before_coll]['kitCanceled'].count()}
    Not Registered before Collection: {data[~registered_before_coll]['kitCanceled'].count()}
    Received on Time: {data[received_on_time]['kitCanceled'].count()}
    Not Received on Time: {data[~received_on_time]['kitCanceled'].count()}"""


# larger function to apply date sorting dunctions to each row in df
def apply_functions(row):
    if pd.notna(row["sampleDelivered"]) and row["sampleDelivered"] == True:
        row["daysDeliveredDiff"] = calc_diff_days(
            row["createdDate"], row["sampleDeliveredDiff"]
        )
        row["deliveredDate"] = date_updated(
            row["createdDate"], row["sampleDeliveredDiff"]
        )
        if pd.isna(row["deliveredDate"]):
            print(row["createdDate"], row["daysDeliveredDiff"])
    else:
        row["daysDeliveredDiff"] = None
        row["deliveredDate"] = None
    if pd.notna(row["sampleReceived"]) and row["sampleReceived"] == True:
        row["daysReceivedDiff"] = calc_diff_days(
            row["createdDate"], row["sampleReceivedDiff"]
        )
        row["receivedDate"] = date_updated(
            row["createdDate"], row["sampleReceivedDiff"]
        )
    else:
        row["daysReceivedDiff"] = None
        row["receivedDate"] = None
    if pd.notna(row["kitRegistered"]) and row["kitRegistered"] == True:
        row["daysRegisteredDiff"] = calc_diff_days(
            row["createdDate"], row["kitRegisteredDiff"]
        )
        row["registeredDate"] = date_updated(
            row["createdDate"], row["kitRegisteredDiff"]
        )
    else:
        row["daysRegisteredDiff"] = None
        row["registeredDate"] = None
    return row


# cleans and prepares the data
def clean_lab_data(in_lab):
    # filter for relevant columns
    in_lab = in_lab[
        [
            "sampleID",
            "spotSku",
            "daysRegisteredDiff",
            "registeredDate",
            "sampleDelivered",
            "daysDeliveredDiff",
            "deliveredDate",
            "sampleReceived",
            "daysReceivedDiff",
            "receivedDate",
            "lastUpdatedDate",
            "collectionRecorded",
            "receivedOnTime",
        ]
    ]
    # filter dates to two weeks ago and round dates
    two_weeks_ago = datetime.today() - timedelta(days=14)
    in_lab = in_lab[in_lab["lastUpdatedDate"] > two_weeks_ago]
    in_lab["lastUpdatedDate"] = in_lab["lastUpdatedDate"].dt.round("min")
    in_lab["receivedDate"] = in_lab["receivedDate"].dt.round("min")
    in_lab["deliveredDate"] = in_lab["deliveredDate"].dt.round("min")
    # filter for extraneous values
    in_lab = in_lab[in_lab["daysDeliveredDiff"] < 30]
    in_lab = in_lab[
        (in_lab["spotSku"] != "quantify_cortisol_kit")
        & (in_lab["spotSku"] != "quantify_dna_methylation_kit")
        & (in_lab["spotSku"] != "quantify_microtainer_collection_kit")
    ]
    # sort
    in_lab = in_lab.sort_values(by="lastUpdatedDate", ascending=False)

    return in_lab


# generates message to be sent in reports
def generate_message(in_lab):
    delivered_not_received = in_lab[
        (in_lab["sampleDelivered"] == True) & (in_lab["sampleReceived"] == False)
    ]["sampleID"].count()
    received_not_delivered = in_lab[
        (in_lab["sampleDelivered"] == False) & (in_lab["sampleReceived"] == True)
    ]["sampleID"].count()

    delivered_received = in_lab[
        (in_lab["sampleDelivered"] == True) & (in_lab["sampleReceived"] == True)
    ]
    not_processed = delivered_received["sampleID"].count()
    less_than_two_days = in_lab[(in_lab["daysReceivedDiff"] < 2.0)]["sampleID"].count()
    two_or_more_days = in_lab[in_lab["daysReceivedDiff"] >= 2.0]["sampleID"].count()
    samples_overdue = in_lab[in_lab["daysRegisteredDiff"] > 5.0]["sampleID"].count()

    today_date = datetime.today().date()
    two_weeks_ago = datetime.today() - timedelta(days=14)

    message = f""" --- DAILY USSL STATISTICS FOR {today_date} ---\n
    Total samples at USSL: {in_lab['daysDeliveredDiff'].count()}\n
    Samples delivered to USSL but not marked received: {delivered_not_received}\n
    Samples marked received but not processed: {not_processed}\n
    Samples not processed for less than two days: {less_than_two_days}\n
    Samples not processed for two days or more: {two_or_more_days}\n
    Samples Overdue (It has been 5+ days since sample registered): {samples_overdue}\n
    Full Datasheet for kits from {two_weeks_ago.date()} to {today_date} can be found below"""

    return message


# manages and runs functions
def main():
    # connect and pull data
    client = connect_mongo()
    docs = pull_mongo_data(client)
    df = pd.DataFrame(docs)

    # filter and mutate data
    df = set_dates(df)
    data = filter_vals(df)
    in_lab = data.apply(apply_functions, axis=1)
    in_lab = clean_lab_data(in_lab)

    # to csv
    path0 = f"all_data.csv"
    in_lab.to_csv(path0, index=False)

    # send data
    message = generate_message(in_lab)
    
    # NOTE: ONLY UNCOMMENT THE FOLLOWING LINES IF YOU ARE READY TO SEND STATISTICS TO SLACK / EMAIL
    #send_slack_message(message, path0)
    #send_email(message, path0)
    return in_lab

# Lambda handler function
def lambda_handler(event, context):
    data = main()
    return {
        'statusCode': 200,
        'body': 'Process completed successfully'
    }

# executes main when running locally
if __name__ == "__main__":
    data = main()