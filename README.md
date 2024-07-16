# ussl-daily-stats

# Overveiew
This repo calculates SiPhox <> SPOT <> USSL Processing Times and has functionality for data cleaning, transformation, and sending the results via Slack and email.

## Prerequisites
- Python 3.10 or later
- Virtual Environment (venv)

## Setup
1. **Clone the repository:**
   ```sh
   git clone <repository-url>
   cd <repository-directory>
   ```
2. **Create and activate virtual environment:**
   python -m venv venv
   .\venv\Scripts\Activate.ps1
3. **Install Dependencies**
    pip install -r requirements.txt

## Usage
python usslstats.py

## Required in .env
MONGO_URI, DB_NAME, COLLECTION_NAME, SLACK_TOKEN, USSL_CHANNEL_ID


#### For lambda integration
mkdir package
pip install --target ./package -r requirements.txt
Copy-Item -Path utils -Destination package/ -Recurse -Force
Copy-Item -Path usslstats.py  -Destination package/ -Force
Compress-Archive -Path package/* -DestinationPath my_lambda_deployment_package.zip   
Then, send to lambda
