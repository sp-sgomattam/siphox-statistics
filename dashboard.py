import streamlit as st
import pandas as pd
import streamlit_pandas as sp
import streamlit_authenticator as stauth
import psutil
import os
import yaml
from datetime import datetime

from prepare_data import prepare_data
from utils.streamlit_utils import generate_dictionary, filter_dataframe

st.set_page_config(page_title="SiPhox Statistics Dashboard", page_icon=":rocket:", layout="wide")


# Load configuration from YAML file
with open('auth.yaml') as file:
    config = yaml.safe_load(file)

# Initialize session state variables
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'name' not in st.session_state:
    st.session_state['name'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'preset_button' not in st.session_state:
    st.session_state.preset_button = False

# Create the authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

# Login and ensure session state is updated
name, authentication_status, username = authenticator.login("main")
st.session_state['authentication_status'] = authentication_status
st.session_state['name'] = name
st.session_state['username'] = username

if st.session_state['authentication_status'] is False:
    st.error("Username/password is incorrect")
elif st.session_state['authentication_status'] is None:
    st.warning("Please enter your username and password")

if st.session_state['authentication_status'] is True:
    st.title("SiPhox Health OPS Dashboard")
    st.write("> *Please note that all metrics are related to SAMPLES unless explicitly stated otherwise*")
    st.write("\n" * 10)
    
    # Function to check memory usage
    def print_memory_usage():
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        st.write(f"Memory usage: {memory_info.rss / 1024 ** 2:.2f} MB")

    # Cache the data preparation step
    @st.cache_data(ttl=1800)
    def load_and_prepare_data():
        df = prepare_data()
        columns = [
            'orderID', 'sampleID', 'businessKey', 'country', 'spotSku', 'spotSkuType', 
            'createdDate', 'kitShippingTime', 'kitRegistered', 'registeredDate', 'targetDate', 'breaksGuarantee', 
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

    # Define preset values
    preset_values = {
        "order_id": "",
        "sample_id": "",
        "business_key": [],
        "spot_sku": [],
        "spot_sku_type": [],
        "country": [],
        "selected_years": [datetime.today().year],
        "selected_months": [datetime.today().month - 1],
        "kit_shipping_time": False,
        "shipping_time": True,
        "lab_processing_time": True,
        "report_publishing_time": False,
        "total_processing_time": False,
        "range_columns": {
            "kitShippingTime": (None, None),
            "shippingTime": (0.49, 31.00),
            "labProcessingTime": (0.10, 30.00),
            "reportPublishingTime": (None, None),
            "totalProcessingTime": (None, None)
        },
        "filter_by_event": False,
        "kit_registered": "ALL",
        "sample_delivered": "ALL",
        "sample_received": "ALL",
        "sample_rejected": "ALL",
        "sample_resulted": "ALL",
        "order_published": "ALL",
        "sample_overdue": "ALL",
        "sample_in_transit": "ALL",
        "sample_processed": "ALL"
    }

    # Button to set preset values
    if st.sidebar.button("Autofill Preset Values "):
        st.session_state.preset_button = True
        st.experimental_rerun()

    # Generate widgets and get filters
    if st.session_state.preset_button:
        filters = generate_dictionary(df, preset_values)
    else:
        filters = generate_dictionary(df)

    if filters is None:
        st.error("Data dictionary is not generated properly.")
        st.stop()

    filtered_df = filter_dataframe(df, filters)

    all_widgets = sp.create_widgets(df, filters, ignore_columns=cols)

    # Calculate averages and display metrics
    time_columns = ["totalProcessingTime", "kitShippingTime", "shippingTime", "labProcessingTime", "reportPublishingTime"]
    column_titles = {
        "kitShippingTime": "Average KIT Shipping Time",
        "shippingTime": "Average SAMPLE Shipping Time",
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
    num_overdue = filtered_df['breaksGuarantee'].sum()
    cols[len(time_columns) + 1].metric(label="Number of Samples Overdue", value=int(num_overdue))

    # Add the Total Samples On Time metric
    num_on_time = (filtered_df['totalProcessingTime'] <= 5).sum()
    cols[len(time_columns) + 2].metric(label="Total Samples On Time (<= 5 days)", value=int(num_on_time))

    st.dataframe(filtered_df)

    # Show Count
    row_count = filtered_df.shape[0]
    st.write(f"Total Count: {row_count}")

    # Create a button to download the DataFrame as a CSV file
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Export as CSV",
        data=csv,
        file_name='data_export.csv',
        mime='text/csv'
    )
    
    st.write("\n" * 10)
    with st.expander("Click to see Definitions", expanded=False):
        st.write("Here are the definitions for our key performance metrics:")
        st.markdown(
            """
            * :hourglass: **Average Total Processing Time:** The average total time from sample collection to report publishing.

            * :package: **Average KIT Shipping Time:** The average time it takes for kits to be shipped. Calculated from kitInTransit to kitDelivered.

            * :package: **Average SAMPLE Shipping Time:** The average time it takes for samples to be shipped. Calculated from the time the sample is dropped off to the time it is delivered/received by USSL.

            * :test_tube: **Average Lab Processing Time:** The average time it takes for the lab to process samples. Calculated from the time the sample is delivered/received by USSL to the time the sample is rejected/resulted.

            * :page_facing_up: **Average Report Publishing Time:** The average time it takes to publish reports. Calculated from the time the sample is rejected/resulted to the time the report is published.

            * :white_check_mark: **Total Samples Processed:** The total number of samples that have been resulted or rejected.

            * :warning: **Number of Samples Overdue:** The number of samples that are overdue. Calculated from the time the user drops off the sample at a USPS store/dropbox to the time the report is published, if this time exceeds 5 days.

            * :white_check_mark: **Total Samples On Time (<= 5 days):** The number of samples processed within the guaranteed timeframe (<= 5 days).

            _Note that all times are calculated using business days. Most American holidays are accounted for._
            """
        )
