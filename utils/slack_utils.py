from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import datetime
import os
import requests
from dotenv import load_dotenv, dotenv_values

load_dotenv()
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
USSL_CHANNEL_ID = os.getenv("USSL_CHANNEL_ID")


# checks slack connection
def check_slack_connection(slack_client):
    auth_test = slack_client.auth_test()
    bot_user_id = auth_test["user_id"]
    print(f"App's bot user: {bot_user_id}")

# sends slack message
def send_slack_message(message, input_file, slack_channel_id = USSL_CHANNEL_ID):
    slack_client  = WebClient(token=SLACK_TOKEN)
    check_slack_connection(slack_client)

    new_file = slack_client.files_getUploadURLExternal(
        filename= input_file,
        length= os.path.getsize(input_file)
    )

    file_id = new_file.get("file_id")
    upload_url= new_file.get('upload_url')
    files = {'file': open(input_file, 'rb')}  # Specify the file you want to upload
    response = requests.post(upload_url, files=files)
    print(response.text)

    new_message = slack_client.files_completeUploadExternal(
        channel_id = slack_channel_id,
        files=[{"id":file_id, "title":f"Data_{datetime.date.today()}"}],
        initial_comment= message
    )
