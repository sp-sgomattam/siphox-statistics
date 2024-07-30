# SIPHOX STATISTICS 

# Overveiew
This repo calculates SiPhox processing statistics of multiple mediums and timeframes. Contact sp-sgomattam with questions/comments/concerns.

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
   .\venv\Scripts\Activate
3. **Install Dependencies**
    pip install -r requirements.txt

## Usage
python daily_stats.py ~ for daily stats
python monthly_stats.py ~ for monthly stats
streamlit dashboard.py ~ for dashboard [IN PROGRESS...]

## Required in .env
- MONGO_URI
- DB_NAME
- COLLECTION_NAME
- SLACK_MONTHLY_TOKEN
- SLACK_DAILY_TOKEN
- USSL_CHANNEL_ID
- OPS_CHANNEL_ID
- TEST_CHANNEL_ID
- ATLAS_PUBLIC_KEY
- ATLAS_PRIVATE_KEY 
- ATLAS_PROJECT_ID

