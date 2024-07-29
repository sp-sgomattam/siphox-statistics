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

def set_keys():
    """Set IP addresses for GitHub Actions in MongoDB Atlas."""
    # Get the MongoDB Atlas credentials from environment variables
    PROJECT_ID = os.getenv('ATLAS_PROJECT_ID', '')
    PUBLIC_KEY = os.getenv('ATLAS_PUBLIC_KEY', '')
    PRIVATE_KEY = os.getenv('ATLAS_PRIVATE_KEY', '')

    # Check if all required environment variables are present and not empty
    if not all([PROJECT_ID, PUBLIC_KEY, PRIVATE_KEY]):
        print("Missing required environment variables for MongoDB Atlas.")
        return

    # Get the list of IP Addresses that GitHub uses
    try:
        response = requests.get('https://api.github.com/meta')
        response.raise_for_status()
        ipAddresses = response.json().get("actions", [])
    except requests.RequestException as e:
        print(f"Failed to retrieve IP addresses from GitHub: {e}")
        return

    # Format the IP Addresses to have associated comments that we will store in Atlas
    data = [{"ipAddress": address, "comment": "IP Address for GitHub Actions"} for address in ipAddresses]

    # Make the POST request to add the IP addresses to the Access List
    try:
        r = requests.post(
            url=f"https://cloud.mongodb.com/api/atlas/v1.0/groups/{PROJECT_ID}/accessList?pretty=true",
            auth=HTTPDigestAuth(str(PUBLIC_KEY), str(PRIVATE_KEY)),
            json=data
        )
        r.raise_for_status()
        # Pretty print the response
        pprint(r.json())
        pprint(r)
    except requests.RequestException as e:
        print(f"Failed to update IP addresses in MongoDB Atlas: {e}")

def main():
    """Main function to execute the script."""
    client = connect_mongo()
    if client:
        documents = pull_mongo_data(client)
        if documents:
            print(f"Retrieved {len(documents)} documents from MongoDB.")
        set_keys()

