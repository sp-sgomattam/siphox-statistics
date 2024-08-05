from slack_sdk import WebClient
import datetime
import os
import requests
from dotenv import load_dotenv

load_dotenv()
USSL_CHANNEL_ID = os.getenv("USSL_CHANNEL_ID")


# checks slack connection
def check_slack_connection(slack_client):
    auth_test = slack_client.auth_test()
    bot_user_id = auth_test["user_id"]
    print(f"App's bot user: {bot_user_id}")

# sends slack message
def send_slack_message(token, message, input_files, slack_channel_id=USSL_CHANNEL_ID):
    slack_client = WebClient(token)
    check_slack_connection(slack_client)

    file_ids = []
    for input_file in input_files:
        new_file = slack_client.files_getUploadURLExternal(
            filename=input_file,
            length=os.path.getsize(input_file)
        )

        file_id = new_file.get("file_id")
        upload_url = new_file.get('upload_url')
        upload_url = new_file.get('upload_url')
        if upload_url:
            files = {'file': open(input_file, 'rb')}  # Specify the file you want to upload
            response = requests.post(upload_url, files=files)
            print(response.text)
        else:
            print(f"Failed to get upload URL for file: {input_file}")
        print(response.text)
        
        file_ids.append({"id": file_id, "title": f"Data_{datetime.date.today()}"})

    new_message = slack_client.files_completeUploadExternal(
        channel_id=slack_channel_id,
        files=file_ids,
        initial_comment=message
    )
