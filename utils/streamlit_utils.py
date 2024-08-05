import streamlit as st
import pandas as pd
from datetime import datetime

def generate_dictionary(df, preset_values=None):
    if preset_values is None:
        preset_values = {}

    # Sidebar widgets
    st.sidebar.header("General Filters")
    
    order_id = st.sidebar.text_input('Order ID', value=preset_values.get("order_id", ""))
    sample_id = st.sidebar.text_input('Sample ID', value=preset_values.get("sample_id", ""))
    
    business_key = st.sidebar.multiselect(
        'Business Key',
        options=df['businessKey'].unique().tolist(),
        default=preset_values.get("business_key", [])
    )
    
    spot_sku = st.sidebar.multiselect(
        'Spot SKU',
        options=df['spotSku'].unique().tolist(),
        default=preset_values.get("spot_sku", [])
    )

    spot_sku_type = st.sidebar.multiselect(
        'Spot SKU Type',
        options=df['spotSkuType'].unique().tolist(),
        default=preset_values.get("spot_sku_type", [])
    )

    country = st.sidebar.multiselect(
        'Country',
        options=df['country'].unique().tolist(),
        default=preset_values.get("country", [])
    )
    
    st.sidebar.header("Date Filters")

    # Multi-select for years and months
    years = list(range(2020, datetime.today().year + 1))
    months = list(range(1, 13))
    
    selected_years = st.sidebar.multiselect("Select Years for Sample Delivered/Received", options=years, default=preset_values.get("selected_years", []))
    selected_months = st.sidebar.multiselect("Select Months for Sample Delivered/Received", options=months, format_func=lambda x: f"{x:02d}", default=preset_values.get("selected_months", []))

    st.sidebar.header("Time Filters")
    st.sidebar.write("*Note that these filters only show items which meet the criteria. Ex: Lab Processing Time only shows items which have been processed by USSL*")

    def range_input(label, min_value, max_value, preset_min=None, preset_max=None):
        min_val = st.sidebar.number_input(f"Min {label}", value=preset_min if preset_min is not None else min_value)
        max_val = st.sidebar.number_input(f"Max {label}", value=preset_max if preset_max is not None else max_value)
        return min_val, max_val

    kit_shipping_time = st.sidebar.checkbox('KIT Shipping Time', value=preset_values.get("kit_shipping_time", False))
    shipping_time = st.sidebar.checkbox('USPS Shipping Time', value=preset_values.get("shipping_time", False))
    lab_processing_time = st.sidebar.checkbox('USSL Processing Time', value=preset_values.get("lab_processing_time", False))
    report_publishing_time = st.sidebar.checkbox('SiPhox Publishing Time', value=preset_values.get("report_publishing_time", False))
    total_processing_time = st.sidebar.checkbox('Total Processing Time', value=preset_values.get("total_processing_time", False))

    range_columns = {
        "kitShippingTime": range_input('KIT Shipping Time', df['shippingTime'].min(), df['shippingTime'].max(), *preset_values.get("range_columns", {}).get("kitShippingTime", (None, None))) if kit_shipping_time else (None, None),
        "shippingTime": range_input('Shipping Time', df['shippingTime'].min(), df['shippingTime'].max(), *preset_values.get("range_columns", {}).get("shippingTime", (None, None))) if shipping_time else (None, None),
        "labProcessingTime": range_input('Lab Processing Time', df['labProcessingTime'].min(), df['labProcessingTime'].max(), *preset_values.get("range_columns", {}).get("labProcessingTime", (None, None))) if lab_processing_time else (None, None),
        "reportPublishingTime": range_input('Report Publishing Time', df['reportPublishingTime'].min(), df['reportPublishingTime'].max(), *preset_values.get("range_columns", {}).get("reportPublishingTime", (None, None))) if report_publishing_time else (None, None),
        "totalProcessingTime": range_input('Total Processing Time', df['totalProcessingTime'].min(), df['totalProcessingTime'].max(), *preset_values.get("range_columns", {}).get("totalProcessingTime", (None, None))) if total_processing_time else (None, None)
    }

    st.sidebar.header("Other")

    # Checkbox for filtering by event
    filter_by_event = st.sidebar.checkbox("Filter by Individual Event", value=preset_values.get("filter_by_event", False))

    if filter_by_event:
        def boolean_select(label, preset_value):
            return st.sidebar.selectbox(label, options=['ALL', 'True', 'False'], index=['ALL', 'True', 'False'].index(preset_value))

        kit_registered = boolean_select('Kit Registered', preset_values.get("kit_registered", "ALL"))
        sample_delivered = boolean_select('Sample Delivered', preset_values.get("sample_delivered", "ALL"))
        sample_received = boolean_select('Sample Received', preset_values.get("sample_received", "ALL"))
        sample_rejected = boolean_select('Sample Rejected', preset_values.get("sample_rejected", "ALL"))
        sample_resulted = boolean_select('Sample Resulted', preset_values.get("sample_resulted", "ALL"))
        order_published = boolean_select('Order Published', preset_values.get("order_published", "ALL"))
        sample_overdue = boolean_select('Sample Overdue', preset_values.get("sample_overdue", "ALL"))
        sample_in_transit = boolean_select('Sample In Transit', preset_values.get("sample_in_transit", "ALL"))
        sample_processed = boolean_select('Sample Processed', preset_values.get("sample_processed", "ALL"))
    else:
        kit_registered = sample_delivered = sample_received = sample_rejected = sample_resulted = order_published = sample_overdue = sample_in_transit = sample_processed = None

    # Initialize the dictionary
    data_dict = {
        "orderID": order_id,
        "sampleID": sample_id,
        "businessKey": business_key,
        "country": country,
        "spotSku": spot_sku,
        "spotSkuType": spot_sku_type,
        "createdDate": None,
        "kitRegistered": kit_registered,
        "registeredDate": None,
        "targetDate": None,
        "breaksGuarantee": sample_overdue,
        "sampleInTransit": sample_in_transit,
        "droppedOffDate": None,
        "sampleDelivered": sample_delivered,
        "deliveredDate": None,
        "sampleReceived": sample_received,
        "receivedDate": None,
        "sampleProcessed": sample_processed,
        "sampleResulted": sample_resulted,
        "resultedDate": None,
        "sampleRejected": sample_rejected,
        "rejectedDate": None,
        "orderPublished": order_published,
        "publishedDate": None,
        "kitShippingTime": range_columns["kitShippingTime"],
        "shippingTime": range_columns["shippingTime"],
        "labProcessingTime": range_columns["labProcessingTime"],
        "reportPublishingTime": range_columns["reportPublishingTime"],
        "totalProcessingTime": range_columns["totalProcessingTime"],
        "selectedYears": selected_years,  # Include the selected years in the dictionary
        "selectedMonths": selected_months  # Include the selected months in the dictionary
    }

    if df.empty:
        st.sidebar.error("The DataFrame is empty. Please adjust the filters or data source.")
        return data_dict

    return data_dict

def filter_dataframe(df, filters):
    # Ensure date columns are in datetime format
    if "sampleDelivered" in df.columns:
        df['sampleDelivered'] = pd.to_datetime(df['sampleDelivered'], errors='coerce')
    if "sampleReceived" in df.columns:
        df['sampleReceived'] = pd.to_datetime(df['sampleReceived'], errors='coerce')

    if filters["orderID"]:
        df = df[df["orderID"].str.contains(filters["orderID"], na=False)]
    if filters["sampleID"]:
        df = df[df["sampleID"].str.contains(filters["sampleID"], na=False)]
    if filters["businessKey"]:
        df = df[df["businessKey"].isin(filters["businessKey"])]
    if filters["country"]:
        df = df[df["country"].isin(filters["country"])]
    if filters["spotSku"]:
        df = df[df["spotSku"].isin(filters["spotSku"])]
    if filters["spotSkuType"]:
        df = df[df["spotSkuType"].isin(filters["spotSkuType"])]

    bool_columns = ["kitRegistered", "sampleDelivered", "sampleReceived", 
                    "sampleRejected", "sampleResulted", "orderPublished", 
                    "breaksGuarantee", "sampleInTransit", "sampleProcessed"]

    for col in bool_columns:
        if filters[col] != 'ALL':
            if filters[col] == 'True':
                df = df[df[col] == True]
            elif filters[col] == 'False':
                df = df[df[col] == False]

    range_columns = ["kitShippingTime", "shippingTime", "labProcessingTime", "reportPublishingTime", "totalProcessingTime"]
    for col in range_columns:
        min_val, max_val = filters[col]
        if min_val is not None and max_val is not None:
            df = df[df[col].notnull() & (df[col] >= min_val) & (df[col] <= max_val)]

    # Filter by selected years and months for sampleDelivered/sampleReceived
    if filters["selectedYears"]:
        # Filter by years only
        if not filters["selectedMonths"]:
            df = df[
                (df["deliveredDate"].dt.year.isin(filters["selectedYears"])) |
                (df["receivedDate"].dt.year.isin(filters["selectedYears"]))
            ]
        # Filter by both years and months
        else:
            df = df[
                ((df["deliveredDate"].dt.year.isin(filters["selectedYears"])) & 
                (df["deliveredDate"].dt.month.isin(filters["selectedMonths"]))) |
                ((df["receivedDate"].dt.year.isin(filters["selectedYears"])) & 
                (df["receivedDate"].dt.month.isin(filters["selectedMonths"])))
            ]

    # Handle case when only months are selected (if needed)
    if filters["selectedMonths"] and not filters["selectedYears"]:
        df = df[
            (df["deliveredDate"].dt.month.isin(filters["selectedMonths"])) |
            (df["receivedDate"].dt.month.isin(filters["selectedMonths"]))
        ]

    return df.reset_index(drop=True)  # Reset index after filtering
