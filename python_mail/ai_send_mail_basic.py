import os, json, base64, re
from transformers import AutoModelForCausalLM, AutoTokenizer
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# 1. Load Qwen locally
model_name = "Qwen/Qwen3-0.6B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

def parse_email_request(user_input: str):
    prompt = f"""
    You are an assistant that outputs ONLY valid JSON.
    Keys: receiver, subject, body.
    Request: "{user_input}"
    Example: {{"receiver": "Bob", "subject": "nice to meet you", "body": "I am your coworker now!"}}
    """

    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=200)

    # Slice off the prompt length to get only new tokens
    generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

    # Regex to extract JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception as e:
            print("⚠️ JSON parse failed:", e)
            print("Raw output:", text)
            return {"receiver": None, "subject": "Unparsed", "body": text}
    else:
        print("⚠️ No JSON found, raw output was:")
        print(text)
        return {"receiver": None, "subject": "Unparsed", "body": text}

# 2. Gmail API setup
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

# 3. Combine everything
if __name__ == "__main__":
    print("Please tell me what should be in your mail and to whom you want to send it")
    user_input = input().strip()
    parsed = parse_email_request(user_input)

    # Map receiver name to actual email
    contacts = {
        "Alice": "stonetsai96@gmail.com",
        "Me": "stonetsai96@gmail.com"
    }

    to_address = contacts.get(parsed.get("receiver"))
    if not to_address:
        print("❌ Failing to send email, cannot find whom to send to!")
    else:
        send_email(to_address, parsed.get("subject", "No Subject"), parsed.get("body", ""))
