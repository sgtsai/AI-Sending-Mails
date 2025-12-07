import json
import random

names = ["alice", "bob", "caixintong", "jim", "tom", "susan", "mike", "linda", "kevin", "sarah"]
domains = ["gs.ncku.edu.tw", "gmail.com", "company.com", "student.ncku.edu.tw", "example.com"]

subjects = [
    "Meeting tomorrow", "Project kickoff", "Reschedule request", "Agenda attached",
    "Welcome aboard", "Check-in", "PR approved", "Thanks", "Reminder", "Follow-up"
]

bodies = [
    "Let's meet at 10am.", "We have started the project.", "Can we move to next Monday?",
    "Please review the agenda.", "Great to have you with us.", "Let's touch base at noon.",
    "Your PR is approved, great work!", "Appreciate your help on this.", "Don't forget the deadline.",
    "Looking forward to your reply."
]

actions = ["add", "update", "delete"]

def random_email(name):
    domain = random.choice(domains)
    return f"{name}@{domain}"

def make_update_example(name):
    action = random.choice(actions)
    email = random_email(name)
    instruction = ""
    if action == "add":
        instruction = f"Add {name} with email {email}"
    elif action == "update":
        instruction = f"Update {name}'s email to {email}"
    elif action == "delete":
        instruction = f"Delete {name} from contacts"
    return {
        "instruction": instruction,
        "output": {"type": "update", "action": action, "name": name, "email": email}
    }

def make_email_example(name):
    email = random_email(name)
    subject = random.choice(subjects)
    body = random.choice(bodies)
    instruction = f"Send {name} an email saying {body}"
    return {
        "instruction": instruction,
        "output": {"type": "email", "receiver": email, "subject": subject, "body": body}
    }

def generate_dataset(n=500):
    dataset = []
    for _ in range(n):
        name = random.choice(names)
        if random.random() < 0.5:
            dataset.append(make_update_example(name))
        else:
            dataset.append(make_email_example(name))
    return dataset

if __name__ == "__main__":
    data = generate_dataset(1000)  # generate 1000 examples
    with open("dataset.jsonl", "w", encoding="utf-8") as f:
        for ex in data:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print("✅ Generated dataset.jsonl with", len(data), "examples")
