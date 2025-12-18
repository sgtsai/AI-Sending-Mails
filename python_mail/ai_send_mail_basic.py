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
        "王士豪": "shyhhau@gmail.com",
        "郭耀煌": "kuoyh@ismp.csie.ncku.edu.tw",
        "謝孫源": "hsiehsy@mail.ncku.edu.tw",
        "連震杰": "jjlien@csie.ncku.edu.tw",
        "楊中平": "cpyoung@mail.csie.ncku.edu.tw",
        "梁勝富": "sfliang@mail.ncku.edu.tw",
        "李同益": "tonylee@mail.ncku.edu.tw",
        "吳宗憲": "chunghsienwu@gmail.com",
        "黃崇明": "huangcm@locust.csie.ncku.edu.tw",
        "陳裕民": "ymchen@mail.ncku.edu.tw",
        "陳響亮": "slchen@mail.ncku.edu.tw",
        "蔣榮先": "jchiang@mail.ncku.edu.tw",
        "陳培殷": "pychen@mail.ncku.edu.tw",
        "鄭憲宗": "stevecheng1688@gmail.com",
        "楊大和": "tyang@mail.ncku.edu.tw",
        "蘇文鈺": "alvinsu@mail.ncku.edu.tw",
        "張燕光": "ykchang@mail.ncku.edu.tw",
        "蘇銓清": "suecc@mail.ncku.edu.tw",
        "蕭宏章": "hchsiao@csie.ncku.edu.tw",
        "盧文祥": "whlu@mail.ncku.edu.tw",
        "張大緯": "davidchang@csie.ncku.edu.tw",
        "藍崑展": "9602016@gs.ncku.edu.tw",
        "賀保羅": "paulh@iscb.org",
        "朱威達": "wtchu@gs.ncku.edu.tw",
        "陳朝鈞": "chencc@imis.ncku.edu.tw",
        "蔡佩璇": "phtsai@mail.ncku.edu.tw",
        "洪昌鈺": "horng@mail.csie.ncku.edu.tw",
        "李政德": "chengte@ncku.edu.tw",
        "許靜芳": "hsucf@csie.ncku.edu.tw",
        "吳明龍": "minglong.wu@csie.ncku.edu.tw",
        "莊坤達": "ktchuang@mail.ncku.edu.tw",
        "涂嘉恒": "chiaheng@ncku.edu.tw",
        "陳奇業": "chency@mail.csie.ncku.edu.tw",
        "曾繁勛": "tsengfh@gs.ncku.edu.tw",
        "何建忠": "ccho@gs.ncku.edu.tw",
        "許舒涵": "shhsu@gs.ncku.edu.tw",
        "詹慧伶": "hlchan@gs.ncku.edu.tw",
        "謝昀珊": "yshsieh@gs.ncku.edu.tw",
        "郭紘睿": "hjguo@gs.ncku.edu.tw",
        "郭軒安": "hsuanankuo@gs.ncku.edu.tw",
        "李信杰": "jielee@mail.ncku.edu.tw",
        "張瑞紘": "changrh@ncku.edu.tw"
    }


    to_address = contacts.get(parsed.get("receiver"))
    if not to_address:
        print("❌ Failing to send email, cannot find whom to send to!")
    else:
        send_email(to_address, parsed.get("subject", "No Subject"), parsed.get("body", ""))
