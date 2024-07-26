import streamlit as st

def generate_dictionary(df):
    # Sidebar widgets
    order_id = st.sidebar.text_input('Order ID')
    sample_id = st.sidebar.text_input('Sample ID')
    
    business_key = st.sidebar.multiselect(
        'Business Key',
        options=df['businessKey'].unique().tolist(),
    )

    spot_sku = st.sidebar.multiselect(
        'Spot SKU',
        options=df['spotSkuType'].unique().tolist(),
    )

    country = st.sidebar.multiselect(
        'Country',
        options=df['country'].unique().tolist(),
    )

    # Initialize the dictionary
    data_dict = {
        "orderID": None,
        "sampleID": None,
        "businessKey": None,
        "country": None,
        "spotSkuType": None,
        "createdDate": None,
        "kitRegistered": None,
        "registeredDate": None,
        "targetDate": None,
        "sampleOverdue": None,
        "sampleInTransit": None,
        "droppedOffDate": None,
        "sampleDelivered": None,
        "deliveredDate": None,
        "sampleReceived": None,
        "receivedDate": None,
        "sampleProcessed": None,
        "sampleResulted": None,
        "resultedDate": None,
        "sampleRejected": None,
        "rejectedDate": None,
        "orderPublished": None,
        "publishedDate": None,
        "shippingTime": None,
        "labProcessingTime": None,
        "reportPublishingTime": None,
        "totalProcessingTime": None
    }

    if df.empty:
        st.sidebar.error("The DataFrame is empty. Please adjust the filters or data source.")
        return data_dict

    # Check if each column has True values
    has_sample_delivered = df['sampleDelivered'].eq(True).any()
    has_sample_received = df['sampleReceived'].eq(True).any()
    has_sample_rejected = df['sampleRejected'].eq(True).any()
    has_sample_resulted = df['sampleResulted'].eq(True).any()

    # Individual date range selectors and days___Diff sliders
    filter_delivered = st.sidebar.checkbox('Filter by Sample Delivered', disabled=df.empty or not has_sample_delivered)
    filter_received = st.sidebar.checkbox('Filter by Sample Received', disabled=df.empty or not has_sample_received)
    filter_rejected = st.sidebar.checkbox('Filter by Sample Rejected', disabled=df.empty or not has_sample_rejected)
    filter_resulted = st.sidebar.checkbox('Filter by Sample Resulted', disabled=df.empty or not has_sample_resulted)

    if not has_sample_delivered:
        st.sidebar.error("No data available for 'Sample Delivered'.")
    elif filter_delivered:
        data_dict["deliveredDateRange"] = st.sidebar.date_input(
            "Delivered Date Range",
            value=(df["deliveredDate"].min(), df["deliveredDate"].max()),
            help="Select a single date or a range of dates"
        )
        data_dict["daysDeliveredDiff"] = st.sidebar.slider(
            "Days Delivered Diff",
            min_value=0.0,
            max_value=float(df["daysDeliveredDiff"].max(skipna=True)),
            value=(0.0, float(df["daysDeliveredDiff"].max(skipna=True))),
            step=0.1
        )

    if not has_sample_received:
        st.sidebar.error("No data available for 'Sample Received'.")
    elif filter_received:
        data_dict["receivedDateRange"] = st.sidebar.date_input(
            "Received Date Range",
            value=(df["receivedDate"].min(), df["receivedDate"].max()),
            help="Select a single date or a range of dates"
        )
        data_dict["daysReceivedDiff"] = st.sidebar.slider(
            "Days Received Diff",
            min_value=0.0,
            max_value=float(df["daysReceivedDiff"].max(skipna=True)),
            value=(0.0, float(df["daysReceivedDiff"].max(skipna=True))),
            step=0.1
        )
        
    if not has_sample_rejected:
        st.sidebar.error("No data available for 'Sample Rejected'.")
    elif filter_rejected:
        data_dict["sampleRejected"] = True

    if not has_sample_resulted:
        st.sidebar.error("No data available for 'Sample Resulted'.")
    elif filter_resulted:
        data_dict["resultedDateRange"] = st.sidebar.date_input(
            "Resulted Date Range",
            value=(df["resultedDate"].min(), df["resultedDate"].max()),
            help="Select a single date or a range of dates"
        )
        data_dict["daysResultedDiff"] = st.sidebar.slider(
            "Days Resulted Diff",
            min_value=0.0,
            max_value=float(df["daysResultedDiff"].max(skipna=True)),
            value=(0.0, float(df["daysResultedDiff"].max(skipna=True))),
            step=0.1
        )
        

    # Unified date range selector if all checkboxes are checked
    if filter_delivered and filter_received and filter_resulted and has_sample_delivered and has_sample_received and has_sample_resulted:
        st.sidebar.markdown("### Unified Date Filter")
        data_dict["unifiedDateRange"] = st.sidebar.date_input(
            "Unified Date Range",
            value=(df[['deliveredDate', 'receivedDate', 'resultedDate']].min().min(), 
                df[['deliveredDate', 'receivedDate', 'resultedDate']].max().max()),
            help="Select a single date or a range of dates"
        )
    
    return data_dict
