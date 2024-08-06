import os
from dotenv import load_dotenv
import pandas as pd
import pymongo
from pymongo.errors import PyMongoError


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
        projection = {
            "lastUpdatedDate": 1, "createdDate": 1, "sampleDelivered": 1, "sampleReceived": 1,
            "sampleCollectionException": 1, "sampleDeliveryException": 1, "sampleCanceled": 1,
            "kitCanceled": 1, "sampleProcessed": 1, "sampleResulted": 1, "sampleRejected": 1,
            "collectionRecorded": 1, "sampleReceivedDiff": 1, "kitRegisteredDiff": 1,
            "kitInTransit": 1, "kitInTransitDiff": 1, "kitDelivered": 1, "kitDeliveredDiff": 1,
            "kitRegistered": 1, "sampleInTransit": 1, "sampleInTransitDiff": 1,
            "sampleDeliveredDiff": 1, "sampleResultedDiff": 1, "sampleRejectedDiff": 1,
            "orderPublished": 1, "orderPublishedDiff": 1, "sampleID": 1, "spotSku": 1,
            "spotSkuType": 1, "orderID": 1, "businessKey": 1, "country": 1,
            "registeredDate": 1, "targetDate": 1, "breaksGuarantee": 1, "droppedOffDate": 1,
            "deliveredDate": 1, "receivedDate": 1, "resultedDate": 1, "rejectedDate": 1,
            "publishedDate": 1, "shippingTime": 1, "labProcessingTime": 1, "reportPublishingTime": 1,
            "totalProcessingTime": 1, "kitShippingTime": 1, "sampleCollectedDiff": 1
        }
        documents = collection.find({}, projection)
        pd.set_option('display.max_columns', None)
        documents_list = list(documents)
        return documents_list
    else:
        print("No MongoDB client available.")
        return []
