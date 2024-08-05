import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()
ZAPIER_EMAIL_WEBHOOK = os.getenv("ZAPIER_EMAIL_WEBHOOK")
ZAPIER_TABLE_WEBHOOK = os.getenv("ZAPIER_TABLE_WEBHOOK")


# sends webhook to Zapier to then format and send email
def send_email(message, file):
    # Send webhook
    with open(file, 'rb') as f:
        encoded_csv = base64.b64encode(f.read()).decode('utf-8')
    data = {
        'message': message,
        'csv': encoded_csv
    }

    if ZAPIER_EMAIL_WEBHOOK:
        response = requests.post(ZAPIER_EMAIL_WEBHOOK, json=data)
        print(response.status_code)
        print(response.text)
    else:
        print("Invalid Zapier email webhook URL")


def update_zapier_table(file):
    # Send webhook
    with open(file, 'rb') as f:
        encoded_csv = base64.b64encode(f.read()).decode('utf-8')
    data = {
        'csv': encoded_csv
    }

    if ZAPIER_TABLE_WEBHOOK:
        response = requests.post(ZAPIER_TABLE_WEBHOOK, json=data)
        print(response.status_code)
        print(response.text)
    else:
        print("Invalid Zapier table webhook URL")
