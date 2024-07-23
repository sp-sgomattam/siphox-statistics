import pandas as pd
from datetime import datetime, timedelta

from prepare_data import prepare_data
from utils.date_utils import calc_diff_days2
from utils.slack_utils import send_slack_message
from utils.zapier_utils import send_email

def filter_daily(df):
    df = df[(df["sampleResulted"] == False) & (df["sampleRejected"] == False)]
    df = df[[
            "sampleID",
            "spotSku",
            "daysSinceRegistered",
            "registeredDate",
            "daysSinceTransit",
            "droppedOffDate",
            "sampleDelivered",
            "daysSinceDelivered",
            "deliveredDate",
            "sampleReceived",
            "daysSinceReceived",
            "receivedDate",
            "lastUpdatedDate",
            "sampleOverdue",
            "collectionRecorded",
            "receivedOnTime",
        ]]
    
    # filter dates to two weeks/months ago and round dates
    two_weeks_ago = datetime.today() - timedelta(days=14)
    two_months_ago = datetime.today() - timedelta(days=60)

    df = df[df["lastUpdatedDate"] > two_weeks_ago]
    # filter for extraneous values
    df = df[df["daysSinceDelivered"] < 30]
    df = df[df["droppedOffDate"] > two_months_ago]
    
    return df

# sanity check to ensure statistics are in order
def statistics_sanity_check(data):
    kit_registered = data["daysSinceRegistered"].notna()
    sample_collected = data["daysSinceReceived"].notna()
    registered_before_coll = data["daysSinceRegistered"] <= data["daysSinceReceived"]
    received_on_time = data["daysSinceReceived"] - data["daysSinceRegistered"] <= 14

    statistics = f"""Total number: {data['sampleID'].count()}
    Registered: {data[kit_registered]['sampleID'].count()}
    Not Registered: {data[~kit_registered]['sampleID'].count()}
    Collection Recorded: {data[sample_collected]['sampleID'].count()}
    Collection Not Recorded: {data[~sample_collected]['sampleID'].count()}
    Registered before Collection: {data[registered_before_coll]['sampleID'].count()}
    Not Registered before Collection: {data[~registered_before_coll]['sampleID'].count()}
    Received on Time: {data[received_on_time]['sampleID'].count()}
    Not Received on Time: {data[~received_on_time]['sampleID'].count()}"""


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
    less_than_two_days = in_lab[(in_lab["daysSinceReceived"] < 2.0)]["sampleID"].count()
    two_or_more_days = in_lab[in_lab["daysSinceReceived"] >= 2.0]["sampleID"].count()
    samples_overdue = in_lab[in_lab["sampleOverdue"] == True]

    overdue_max = 0
    overdue_med = 0
    overdue_low = 0

    for index, row in samples_overdue.iterrows():
        days_overdue = calc_diff_days2(row["droppedOffDate"], datetime.today())
        if days_overdue < 7.0:
            overdue_low += 1
        elif days_overdue < 12:
            overdue_med += 1
        else:
            overdue_max += 1

    today_date = datetime.today().date()
    two_weeks_ago = datetime.today() - timedelta(days=14)

    message = f"""
        *--- DAILY USSL STATISTICS FOR {today_date} ---*
        
        📊 *Total samples at USSL:* *{in_lab['sampleID'].count()}*
        
        ------------------------------------------------------------------------------
        📦 USSL Pickup Time:

            Samples delivered to USSL but not marked as received: *{delivered_not_received}*
            Samples received but not yet processed: *{not_processed}*
        
        ------------------------------------------------------------------------------
        ⏳ USSL Processing Time:

            Samples received for <2 days: *{less_than_two_days}*       
            Samples received for >=2 days: *{two_or_more_days}*
        
        ------------------------------------------------------------------------------

        ⚠️ *Samples Overdue:* *{samples_overdue['sampleID'].count()}*
        _Categorized by business days since the user has dropped the sample off (we promise 3-5)_

            Samples overdue for <7 days: *{overdue_low}*      
            Samples overdue for <12 days: *{overdue_med}*       
            Samples overdue for >=12 days: *{overdue_max}*

        *Full Datasheet for kits from {two_weeks_ago.date()} to {today_date} can be found below
        """

    return message


# manages and runs functions
def main():
    # connect and pull data
    df = prepare_data()
    in_lab = filter_daily(df)
    
    # to csv
    path0 = f"all_data.csv"
    in_lab.to_csv(path0, index=False)

    # send data
    message = generate_message(in_lab)

    # NOTE: ONLY UNCOMMENT THE FOLLOWING LINES IF YOU ARE READY TO SEND STATISTICS TO SLACK / EMAIL
    # test id: C07DE075ZLG
    send_slack_message(message, path0, "C07DE075ZLG")
    #send_slack_message(message, path0)
    #send_email(message, path0)
    return in_lab


# Lambda handler function
def lambda_handler(event, context):
    data = main()
    return {"statusCode": 200, "body": "Process completed successfully"}


# executes main when running locally
if __name__ == "__main__":
    data = main()
