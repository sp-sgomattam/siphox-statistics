import streamlit as st
import pandas as pd
import streamlit_pandas as sp
import psutil
import os

from prepare_data import prepare_data
from utils.streamlit_utils import generate_dictionary, filter_dataframe
st.set_page_config(layout="wide")
st.title("SiPhox Health OPS Dashboard")

# Function to check memory usage
def print_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    st.write(f"Memory usage: {memory_info.rss / 1024 ** 2:.2f} MB")

# Cache the data preparation step
@st.cache_data
def load_and_prepare_data():
    df = prepare_data()
    columns = [
        'orderID', 'sampleID', 'businessKey', 'country', 'spotSku', 'spotSkuType', 
        'createdDate', 'kitRegistered', 'registeredDate', 'targetDate', 'sampleOverdue', 
        'sampleInTransit', 'droppedOffDate', 'sampleDelivered', 'deliveredDate', 
        'sampleReceived', 'receivedDate', 'sampleProcessed', 'sampleResulted', 
        'resultedDate', 'sampleRejected', 'rejectedDate', 'orderPublished', 
        'publishedDate', 'shippingTime', 'labProcessingTime', 'reportPublishingTime', 
        'totalProcessingTime'
    ]

    selected_columns = df[columns]
    return selected_columns


df = load_and_prepare_data()
cols = []

data_dictionary = generate_dictionary(df)
if data_dictionary is None:
    st.error("Data dictionary is not generated properly.")
    st.stop()

filtered_df = filter_dataframe(df, data_dictionary)

all_widgets = sp.create_widgets(df, data_dictionary, ignore_columns=cols)

# Calculate averages and display metrics
time_columns = ["shippingTime", "labProcessingTime", "reportPublishingTime", "totalProcessingTime"]
column_titles = {
    "shippingTime": "Average Shipping Time",
    "labProcessingTime": "Average Lab Processing Time",
    "reportPublishingTime": "Average Report Publishing Time",
    "totalProcessingTime": "Average Total Processing Time"
}

# Create columns for metrics
cols = st.columns(len(time_columns) + 3)  # Add extra columns for the new metrics

for col, time_col in zip(cols[:len(time_columns)], time_columns):
    if time_col in filtered_df.columns:
        avg_value = filtered_df[time_col].mean()
        col.metric(label=column_titles[time_col], value=f"{avg_value:.2f}")
        
# Add the Total Samples Processed metric
num_processed = filtered_df['sampleProcessed'].sum()
cols[len(time_columns)].metric(label="Total Samples Processed", value=int(num_processed))

# Add the Number of Samples Overdue metric
num_overdue = filtered_df['sampleOverdue'].sum()
cols[len(time_columns) + 1].metric(label="Number of Samples Overdue", value=int(num_overdue))


# Add the Total Samples On Time metric
num_on_time = (filtered_df['totalProcessingTime'] <= 5).sum()
cols[len(time_columns) + 2].metric(label="Total Samples On Time (<= 5 days)", value=int(num_on_time))



st.dataframe(filtered_df)

# Show Count
row_count = filtered_df.shape[0]
st.write(f"Total Count: {row_count}")

# Create a button to download the DataFrame as a CSV file
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Export as CSV",
    data=csv,
    file_name='data_export.csv',
    mime='text/csv'
)
