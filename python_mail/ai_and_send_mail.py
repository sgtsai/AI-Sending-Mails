import os, json, base64
from transformers import AutoModelForCausalLM, AutoTokenizer
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from pydantic import BaseModel, EmailStr, ValidationError
from typing import Literal
from peft import PeftModel   # ✅ added for LoRA

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# --- Load Qwen with LoRA adapter ---
model_name = "Qwen/Qwen3-0.6B"
adapter_dir = "./qwen-lora-json"   # path to your trained adapter

tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
base_model = AutoModelForCausalLM.from_pretrained(model_name)
model = PeftModel.from_pretrained(base_model, adapter_dir)
model.eval()

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

# --- Helper: Extract JSON block ---
def extract_json(text: str):
    text += " "
    start = text.find("{")
    end = text.find("}")
    if start != -1 and end != -1:
        candidate = text[start:end+1]
        try:
            return json.loads(candidate)
        except Exception as e:
            print("⚠️ JSON parse failed:", e)
            return None
    return None

# --- Parsing unified request ---
def parse_request(user_input: str, contacts: dict):
    prompt = f"""
    Give me ONLY EXACTLY one JSON object. No explanations, no quotes, no markdown fences, no extra text.
    You have access to the following contacts: {contacts}
    Request: "{user_input}"
    If you give me anything other than JSON, my program to read your output:
    extract_json(text: str) would fail, so output only JSON object base on the Request:
    Case1: If it's a contact update: {{"type":"update","action":"add/update/delete","name":"...","email":"..."}}
    Example output: {{"type":"update","action":"add","name":"Jim","email":"s110467student@gmail.com"}}
    Case2: If it's an email: {{"type":"email","receiver":"<actual email address>","subject":"...","body":"..."}}
    Example output: {{"type":"email","receiver":"stonetsai96@gmail.com","subject":"hello","body":"hi"}}
    """

    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=200)
    generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

    print("=== Raw AI output ===")
    print(text)

    parsed_json = extract_json(text)
    if not parsed_json:
        print("⚠️ No valid JSON found")
        return None

    # Try validating against each schema
    try:
        return EmailRequest.parse_obj(parsed_json)
    except ValidationError:
        pass

    try:
        return ContactUpdate.parse_obj(parsed_json)
    except ValidationError:
        pass

    print("⚠️ Validation failed for both schemas")
    return None

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

# --- Main ---
if __name__ == "__main__":
    contacts = {
        "bob": "f74144765@gs.ncku.edu.tw",
        "alice": "stonetsai96@gmail.com",
        "me": "stonetsai96@gmail.com"
    }
    while True:    
        print("Tell me your request (either update contact OR send email), Typing quit would end the program.")
        user_input = input().strip()
        if user_input == "quit":
            break
        parsed = parse_request(user_input, contacts)
        if parsed:
            handle_request(parsed, contacts)
