import os, json, base64
from transformers import AutoModelForCausalLM, AutoTokenizer
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from pydantic import BaseModel, EmailStr, ValidationError, Field
from typing import Annotated, Literal, Union
from peft import PeftModel   # ✅ added for LoRA
from fastapi import FastAPI

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


app = FastAPI()

contacts = {
        "bob": "f74144765@gs.ncku.edu.tw",
        "alice": "stonetsai96@gmail.com",
        "me": "stonetsai96@gmail.com"
    }

# --- Pydantic Schemas ---
class EmailRequest(BaseModel):
    type: Literal["email"]
    receiver: EmailStr   # must be a full email address now
    subject: str
    body: str

class ContactUpdate(BaseModel):
    type: Literal["update"]
    action: Literal["add", "update", "delete"]
    name: str
    email: EmailStr


# --- Gmail API setup ---
def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def send_email(to_address, subject, body_text):
    print(f"to_address: {to_address}, subject: {subject}, body_text: {body_text}")
    service = get_gmail_service()
    message = MIMEText(body_text)
    message['to'] = to_address
    message['from'] = "stonetsai96@gmail.com"
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}
    service.users().messages().send(userId="me", body=body).execute()
    print(f"✅ Email sent to {to_address}")

# --- Contact management ---
def update_contacts(contacts: dict, update: dict):
    action = update.get("action")
    name = update.get("name")
    email = update.get("email")

    if action == "add":
        if name and email:
            contacts[name] = email
            print(f"✅ Added contact {name} -> {email}")
    elif action == "update":
        if name in contacts and email:
            contacts[name] = email
            print(f"✅ Updated contact {name} -> {email}")
        else:
            print(f"❌ Cannot update, {name} not found")
    elif action == "delete":
        if name in contacts:
            del contacts[name]
            print(f"✅ Deleted contact {name}")
        else:
            print(f"❌ Cannot delete, {name} not found")
    else:
        print("❌ Unknown action")

    return contacts

# --- Dispatcher ---
def handle_request(parsed, contacts):
    if isinstance(parsed, ContactUpdate):
        contacts = update_contacts(contacts, parsed.dict())

    elif isinstance(parsed, EmailRequest):
        send_email(parsed.receiver, parsed.subject, parsed.body)

    else:
        print("❌ Unknown request type")

RequestPayload = Annotated[
    Union[EmailRequest, ContactUpdate],
    Field(discriminator="type")
]


@app.post("/dispatcher_and_send_mail")

def dispatcher(payload: RequestPayload):
    print("JSON received!!")
    handle_request(payload, contacts)
