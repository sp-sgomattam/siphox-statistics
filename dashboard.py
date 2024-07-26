import streamlit as st
import pandas as pd
import streamlit_pandas as sp
import psutil
import os

from prepare_data import prepare_data

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
        'orderID', 'sampleID', 'businessKey', 'country', 'spotSkuType', 
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
