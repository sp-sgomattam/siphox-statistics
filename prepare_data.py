import pandas as pd
import numpy as np
from datetime import datetime
from functools import lru_cache
from utils.mongo_utils import *
from utils.date_utils import *

# Cached version of convert_to_est to avoid redundant calculations
@lru_cache(maxsize=None)
def convert_to_est_cached(date, is_dst=True):
    return convert_to_est(date, is_dst)

# Function to set datetime objects and filter dates
def set_dates(df):
    df["lastUpdatedDate"] = pd.to_datetime(df["lastUpdatedDate"]).apply(
        lambda x: convert_to_est_cached(x, is_dst=True)
    )
    df["createdDate"] = pd.to_datetime(df["createdDate"]).apply(
        lambda x: convert_to_est_cached(x, is_dst=True)
    )
    return df

# Function to filter DataFrame based on specific criteria
def filter_vals(df):
    data = df[(df["sampleDelivered"] == True) | (df["sampleReceived"] == True)]
    data = data[
        (data["sampleCollectionException"] == False)
        & (data["sampleDeliveryException"] == False)
        & (data["sampleCanceled"] == False)
        & (data["kitCanceled"] == False)
    ]
    data["sampleProcessed"] = data["sampleResulted"] | data["sampleRejected"]
    data["collectionRecorded"] = data["sampleCollectedDiff"].notna()
    data["receivedOnTime"] = (
        data["sampleReceivedDiff"] - data["kitRegisteredDiff"] <= 14
    )
    return data

# Function to apply various calculations and transformations to the DataFrame
def apply_functions_optimized(df):
    event_names = [
        ("kitRegistered", "kitRegisteredDiff", "registeredDate", "daysSinceRegistered"),
        ("sampleInTransit", "sampleInTransitDiff", "droppedOffDate", "daysSinceTransit"),
        ("sampleDelivered", "sampleDeliveredDiff", "deliveredDate", "daysSinceDelivered"),
        ("sampleReceived", "sampleReceivedDiff", "receivedDate", "daysSinceReceived"),
        ("sampleResulted", "sampleResultedDiff", "resultedDate", "daysSinceResulted"),
        ("sampleRejected", "sampleRejectedDiff", "rejectedDate", "daysSinceRejected"),
        ("orderPublished", "orderPublishedDiff", "publishedDate", "daysSincePublished"),
    ]

    # Calculate date differences and update date columns
    for mongo_event_name, mongo_event_diff, event_date, event_days_diff in event_names:
        df[event_days_diff] = df.apply(
            lambda row: calc_diff_days(row["createdDate"], row[mongo_event_diff])
            if pd.notna(row[mongo_event_name]) and row[mongo_event_name] and pd.notna(row[mongo_event_diff])
            else None, axis=1
        )
        df[event_date] = df.apply(
            lambda row: date_updated(row["createdDate"], row[mongo_event_diff])
            if pd.notna(row[mongo_event_name]) and row[mongo_event_name] and pd.notna(row[mongo_event_diff])
            else None, axis=1
        )

    df["targetDate"] = df["droppedOffDate"].apply(
        lambda x: date_updated(x, 5.0) if pd.notna(x) else None
    )

    # Helper function to calculate time differences
    def calculate_times(row, start_col, end_col):
        return calc_diff_days2(row[start_col], row[end_col]) if pd.notna(row[start_col]) and pd.notna(row[end_col]) else None

    # Calculate various processing times
    df["shippingTime"] = df.apply(lambda row: calculate_times(row, "droppedOffDate", "deliveredDate") or calculate_times(row, "droppedOffDate", "receivedDate"), axis=1)
    df["labProcessingTime"] = df.apply(lambda row: calculate_times(row, "deliveredDate", "resultedDate") or calculate_times(row, "deliveredDate", "rejectedDate") or calculate_times(row, "receivedDate", "resultedDate") or calculate_times(row, "receivedDate", "rejectedDate"), axis=1)
    df["sampleProcessingTime"] = df.apply(lambda row: calculate_times(row, "droppedOffDate", "resultedDate") or calculate_times(row, "droppedOffDate", "rejectedDate"), axis=1)
    df["reportPublishingTime"] = df.apply(lambda row: calculate_times(row, "resultedDate", "publishedDate"), axis=1)
    df["totalProcessingTime"] = df.apply(lambda row: calculate_times(row, "droppedOffDate", "publishedDate"), axis=1)

    # Determine if the sample is overdue
    df["sampleOverdue"] = df.apply(
        lambda row: (calc_diff_days2(row["droppedOffDate"], datetime.today()) > 5.0)
        if pd.notna(row["droppedOffDate"]) and not row["sampleResulted"]
        else (calc_diff_days2(row["droppedOffDate"], row["publishedDate"]) > 5.0)
        if pd.notna(row["droppedOffDate"]) and pd.notna(row["publishedDate"])
        else False, axis=1
    )

    return df

# Function to clean and sort lab data
def clean_lab_data(in_lab):
    in_lab = in_lab[
        ~in_lab["spotSku"].isin(
            [
                "quantify_cortisol_kit",
                "quantify_dna_methylation_kit",
                "quantify_microtainer_collection_kit",
            ]
        )
    ]
    in_lab = in_lab[~((in_lab["status"] == "rejected") & (in_lab["status"] == "resulted"))]

    for col in in_lab.columns:
        if "date" in col.lower():
            in_lab[col] = pd.to_datetime(in_lab[col]).dt.round("min")

    return in_lab.sort_values(by="lastUpdatedDate", ascending=False)

# Main function to prepare data
@lru_cache(maxsize=None)
def prepare_data():
    client = connect_mongo()
    docs = pull_mongo_data(client)
    df = pd.DataFrame(docs)
    df = set_dates(df)
    data = filter_vals(df)
    data = apply_functions_optimized(data)
    data = clean_lab_data(data)
    return data
