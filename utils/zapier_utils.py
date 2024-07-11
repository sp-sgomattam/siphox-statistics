import requests
import json
import base64

# sends webhook to Zapier to then format and send email
def send_email(message, file):
    # Send webhook
    webhook_url = 'https://hooks.zapier.com/hooks/catch/12315584/3vlas4u/'
    with open(file, 'rb') as f:
        encoded_csv = base64.b64encode(f.read()).decode('utf-8')
    data = {"""  """
        'message': message,
        'csv': encoded_csv
    }

    response = requests.post(webhook_url, json=data)
    print(response.status_code)
    print(response.text)