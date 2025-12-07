from __future__ import print_function
import os.path
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API 權限範圍：只需要寄信
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def send_email():
    creds = None
    # 如果之前已經授權過，會有 token.json
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # 如果沒有憑證或憑證失效，重新跑 OAuth 流程
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 儲存憑證，下次就不用再登入
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    # 建立郵件內容
    message = MIMEText("這是一封由 Python + Gmail API 寄出的測試信件")
    message['to'] = "a0985987557@gmail.com"
    message['from'] = "stonetsai96@gmail.com"
    message['subject'] = "測試郵件"

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}

    # 寄出郵件
    service.users().messages().send(userId="me", body=body).execute()
    print("Email sent successfully!")

if __name__ == '__main__':
    send_email()
