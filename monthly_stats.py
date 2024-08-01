import pandas as pd
from datetime import datetime
import numpy as np
import calendar
import os
import matplotlib.pyplot as plt

from prepare_data import prepare_data
from utils.slack_utils import send_slack_message

# Function to process data for specified months of a given year
def process_data_for_months(df, year, months):
    monthly_data = {}

    for month in months:
        # Filter data for the given month and year
        month_data = df[
            ((df["receivedDate"].dt.month == month) & 
            (df["receivedDate"].dt.year == year)) | 
            ((df["rejectedDate"].dt.month == month) & 
            (df["rejectedDate"].dt.year == year))
        ]

        # Calculate statistics for completed samples
        completed_samples = month_data[(month_data['sampleResulted'] == True) | (month_data['sampleRejected'] == True)]
        total_completed_samples = completed_samples.shape[0]
        total_kits_resulted = completed_samples['sampleResulted'].sum()
        total_kits_rejected = completed_samples['sampleRejected'].sum()
        uncounted_kits = total_completed_samples - (total_kits_resulted + total_kits_rejected)
        
        # Generate warnings based on uncounted kits
        warning = ""
        if uncounted_kits > 0:
            warning = f"WARNING: there are {uncounted_kits} samples in this data that are not resulted or rejected"
        elif uncounted_kits < 0:
            warning = f"WARNING: there are {uncounted_kits * -1} samples in this data that are both resulted and rejected"

        # Calculate shipping statistics
        shipped_samples = completed_samples[completed_samples['shippingTime'].notna()]
        kits_shipped_usps = shipped_samples['shippingTime'].notna().sum()
        avg_shipping_time = shipped_samples['shippingTime'].mean().round(2)
        shipped_under_3 = shipped_samples[shipped_samples["shippingTime"] <= 3]['shippingTime'].notna().sum()
        shipped_under_5 = shipped_samples[(shipped_samples["shippingTime"] <= 5) & (shipped_samples["shippingTime"] > 3)]['shippingTime'].notna().sum()
        shipped_over_5 = shipped_samples[shipped_samples["shippingTime"] > 5]['shippingTime'].notna().sum()

        # Calculate lab processing statistics
        processed_samples = completed_samples[completed_samples['labProcessingTime'].notna()]
        samples_processed_ussl = processed_samples['labProcessingTime'].notna().sum()
        avg_lab_processing_time = processed_samples['labProcessingTime'].mean().round(2)
        processed_under_2 = processed_samples[processed_samples["labProcessingTime"] <= 2]['labProcessingTime'].notna().sum()
        processed_under_4 = processed_samples[(processed_samples["labProcessingTime"] <= 4) & (processed_samples["labProcessingTime"] > 2)]['labProcessingTime'].notna().sum()
        processed_over_4 = processed_samples[processed_samples["labProcessingTime"] > 4]['labProcessingTime'].notna().sum()

        # Calculate report publishing statistics
        published_samples = completed_samples[completed_samples['reportPublishingTime'].notna()]
        reports_published_siphox = published_samples['reportPublishingTime'].notna().sum()
        avg_report_publishing_time = published_samples['reportPublishingTime'].mean().round(2)
        published_under_2 = published_samples[published_samples["reportPublishingTime"] <= 2]['reportPublishingTime'].notna().sum()
        published_over_2 = published_samples[published_samples["reportPublishingTime"] > 2]['reportPublishingTime'].notna().sum()

        # Calculate total processing statistics
        avg_total_processing_time = month_data['totalProcessingTime'].mean().round(2)
        samples_overdue = completed_samples[completed_samples['breaksGuarantee'] == True]
        num_samples_overdue = samples_overdue['totalProcessingTime'].notna().sum()
        overdue_under_7 = samples_overdue[(samples_overdue['totalProcessingTime'] < 7) & (samples_overdue['totalProcessingTime'] >= 5)]['totalProcessingTime'].notna().sum()
        overdue_under_12 = samples_overdue[(samples_overdue['totalProcessingTime'] < 12) & (samples_overdue['totalProcessingTime'] >= 7)]['totalProcessingTime'].notna().sum()
        overdue_max = samples_overdue[samples_overdue['totalProcessingTime'] >= 12]['totalProcessingTime'].notna().sum()

        # Store monthly statistics
        monthly_data[month] = {
            "Month": int(month),
            "total_completed_samples": total_completed_samples,
            "total_kits_resulted": total_kits_resulted,
            "total_kits_rejected": total_kits_rejected,
            "kits_shipped_usps": kits_shipped_usps,
            "avg_shipping_time": avg_shipping_time,
            "shipped_under_3": shipped_under_3,
            "shipped_under_5": shipped_under_5,
            "shipped_over_5": shipped_over_5,
            "samples_processed_ussl": samples_processed_ussl,
            "avg_lab_processing_time": avg_lab_processing_time,
            "processed_under_2": processed_under_2,
            "processed_under_4": processed_under_4,
            "processed_over_4": processed_over_4,
            "reports_published_siphox": reports_published_siphox,
            "avg_report_publishing_time": avg_report_publishing_time,
            "published_under_2": published_under_2,
            "published_over_2": published_over_2,
            "avg_total_processing_time": avg_total_processing_time,
            "num_samples_overdue": num_samples_overdue,
            "overdue_under_7": overdue_under_7,
            "overdue_under_12": overdue_under_12,
            "overdue_max": overdue_max,
            "warning": warning,
        }

    return pd.DataFrame(monthly_data).transpose()

import matplotlib.pyplot as plt

def plot_boxplots(df, year, month):
    # Filter data for the given month and year
    current_month_data = df[
        ((df["receivedDate"].dt.month == month) & 
        (df["receivedDate"].dt.year == year)) | 
        ((df["rejectedDate"].dt.month == month) & 
        (df["rejectedDate"].dt.year == year))
    ]
    
    completed_samples = current_month_data[(current_month_data['sampleResulted'] == True) | (current_month_data['sampleRejected'] == True)]
    
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(15, 10))

    # Set the title for the entire figure
    fig.suptitle(f'Month {month} Processing Times', fontsize=16)

    # Plot USPS Shipping Times
    axes[0].boxplot(completed_samples['shippingTime'].dropna(), vert=False, patch_artist=True, showfliers=False)
    axes[0].set_xlabel('Shipping Time (days)')
    axes[0].set_title('USPS Shipping Times')

    # Plot USSL Lab Processing Times
    axes[1].boxplot(completed_samples['labProcessingTime'].dropna(), vert=False, patch_artist=True, showfliers=False)
    axes[1].set_xlabel('Lab Processing Time (days)')
    axes[1].set_title('USSL Lab Processing Times')

    # Plot SiPhox Report Publishing Times
    axes[2].boxplot(completed_samples['reportPublishingTime'].dropna(), vert=False, patch_artist=True, showfliers=False)
    axes[2].set_xlabel('Report Publishing Time (days)')
    axes[2].set_title('SiPhox Report Publishing Times')

    plt.subplots_adjust(hspace=0.5)
    # Save the plot as an image
    image_path = r'files\monthly_processing_times.png'
    plt.savefig(image_path)
    plt.close()

    return image_path

    
def generate_message(latest_row):
    return f"""
    ----------------------------------------------------------------------------------------------
    For month {latest_row['Month']}, the kit processing results are:
    ----------------------------------------------------------------------------------------------
    *GENERAL STATISTICS*
    Total Kits Processed: {latest_row['total_completed_samples']}
    Kits Resulted: {latest_row['total_kits_resulted']}
    Kits Rejected: {latest_row['total_kits_rejected']}
    _{latest_row['warning']}_
    ----------------------------------------------------------------------------------------------
    *USPS SHIPPING*
    Avg Shipping Time: {latest_row['avg_shipping_time']:.2f} days 
    Shipped <= 3 Days: {latest_row['shipped_under_3']}
    Shipped 3-5 Days: {latest_row['shipped_under_5']}
    Shipped > 5 Days: {latest_row['shipped_over_5']}
    ----------------------------------------------------------------------------------------------
    *USSL PROCESSING*
    Avg Lab Processing Time: {latest_row['avg_lab_processing_time']:.2f} days
    Processed <= 2 Days: {latest_row['processed_under_2']}
    Processed 2-4 Days: {latest_row['processed_under_4']}
    Processed > 4 Days: {latest_row['processed_over_4']}
    ----------------------------------------------------------------------------------------------
    *SIPHOX PUBLISHING*
    Avg Report Publishing Time: {latest_row['avg_report_publishing_time']:.2f} days
    Published <= 2 Days:  {latest_row['published_under_2']}
    Published > 2 Days:  {latest_row['published_over_2']}
    ----------------------------------------------------------------------------------------------
    *OVERDUE SAMPLES*
    Avg Total Processing Time: {latest_row['avg_total_processing_time']:.2f} days
    Number of Samples Overdue: {latest_row['num_samples_overdue']}
    Overdue <= 7 Days: {latest_row['overdue_under_7']}
    Overdue 7-12 Days: {latest_row['overdue_under_12']}
    Overdue > 12 Days: {latest_row['overdue_max']}
    ----------------------------------------------------------------------------------------------
    """
    

def main():
    # Prepare data
    df = prepare_data()
    
    df = df[
        ~df["spotSku"].isin(
            [
                "quantify_cortisol_kit",
                "quantify_dna_methylation_kit",
                "quantify_microtainer_collection_kit",
            ]
        )
    ]

    # Define the months to process
    last_month = datetime.now().month - 1
    all_months = list(range(1, last_month + 1))
    all_data = process_data_for_months(df, 2024, all_months)
    
    month_data = df[
            ((df["receivedDate"].dt.month == last_month) & 
            (df["receivedDate"].dt.year == datetime.now().year)) | 
            ((df["rejectedDate"].dt.month == last_month) & 
            (df["rejectedDate"].dt.year == datetime.now().year))
    ]

    month_data_path = r"files\month_data_raw.csv"
    month_data.to_csv(month_data_path, index=False)
    
    # Plot Data
    image = plot_boxplots(df, 2024, last_month)

    # Generate message for the latest month's statistics
    latest_row = all_data.iloc[-1]
    message = generate_message(latest_row)

    # Generate final message with the date
    current_date = datetime.today().strftime("%Y-%m-%d")
    final_message = (
        f"--- KITS RESULTED STATISTICS UP TO {current_date} ---\n\n"
        + message
        + "\n\nPlease see all data and visualizations below"
    )

    # Save the data to a CSV file
    summary_path = r"files\monthly_processing_time_summary.csv"
    all_data.to_csv(summary_path, index=False)

    # Send the message to Slack
    SLACK_MONTHLY_TOKEN = os.getenv("SLACK_MONTHLY_TOKEN")
    OPS_CHANNEL_ID = os.getenv("OPS_CHANNEL_ID")
    TEST_CHANNEL_ID = os.getenv("TEST_CHANNEL_ID")
    send_slack_message(SLACK_MONTHLY_TOKEN, final_message, [summary_path, month_data_path, image], OPS_CHANNEL_ID)

# Execute main function when running the script directly
if __name__ == "__main__":
    data = main()
