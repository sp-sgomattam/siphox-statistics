import os
from dotenv import load_dotenv
import pandas as pd
import pymongo
from pymongo.errors import PyMongoError
import requests
from requests.auth import HTTPDigestAuth
from pprint import pprint

# Load environment variables from .env file
load_dotenv()

# Retrieve MongoDB URI from environment variables
MONGO_URI = os.getenv("MONGO_URI")

def connect_mongo():
    """Connect to MongoDB and return the client."""
    try:
        client = pymongo.MongoClient(MONGO_URI)
        # Verify connection
        client.admin.command('ping')
        print("Connection successful!")
        return client
    except PyMongoError as e:
        print(f"Connection failed: {e}")
        return None

def pull_mongo_data(client):
    """Pull data from MongoDB and return as a list of documents."""
    if client:
        table = client['quantify']
        collection = table['spot-history-statuses']
        documents = collection.find()
        pd.set_option('display.max_columns', None)
        documents_list = list(documents)
        return documents_list
    else:
        print("No MongoDB client available.")
        return []


