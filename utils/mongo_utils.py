
import os
from dotenv import load_dotenv
import pandas as pd
import pymongo

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# connect to monog
def connect_mongo():
    try:
        client = pymongo.MongoClient(MONGO_URI)
        # Verify connection
        print("Connection successful!")
    except pymongo.errors.ConnectionError as e:
        print(f"Connection failed: {e}")

    return client

# pull data from mongo
def pull_mongo_data(client):
    table = client['quantify']
    collection=table['spot-history-statuses']
    documents = collection.find()
    pd.set_option('display.max_columns', None)
    documents_list = list(documents)
    return documents_list
