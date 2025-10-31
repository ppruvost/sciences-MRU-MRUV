#!/usr/bin/env python3
import json
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Read GitHub event payload
event_path = os.environ.get("GITHUB_EVENT_PATH", "/github/workflow/event.json")
with open(event_path, "r", encoding="utf-8") as f:
    event = json.load(f)

issue = event.get("issue", {})
title = issue.get("title", "")
body = issue.get("body", "")

# Extract information from the issue body
def parse_field(text, field_name):
    for line in text.splitlines():
        if line.strip().lower().startswith(field_name.lower() + ":"):
            return line.split(":", 1)[1].strip()
    return ""

last_name = parse_field(body, "Last Name")
first_name = parse_field(body, "First Name")
score = parse_field(body, "Score")
timestamp = parse_field(body, "Timestamp")

if not timestamp:
    timestamp = datetime.utcnow().isoformat() + "Z"

# Environment variables (secrets)
SENDER = os.environ.get("EMAIL_USER")
PASSWORD = os.environ.get("EMAIL_PASS")
RECEIVER = os.environ.get("RECEIVER_EMAIL")

if not all([SENDER, PASSWORD, RECEIVER]):
    print("ERROR: EMAIL_USER, EMAIL_PASS, and RECEIVER_EMAIL must be defined in secrets.")
    raise SystemExit(1)

subject = f"Quiz Results — {first_name} {last_name} — {score}"
html = f"""
<html>
  <body>
    <h2>Quiz Results</h2>
    <p><strong>Last Name:</strong> {last_name}</p>
    <p><strong>First Name:</strong> {first_name}</p>
    <p><strong>Score:</strong> {score}</p>
    <p><strong>Timestamp:</strong> {timestamp}</p>
    <hr>
    <p>GitHub Issue: <a href="{issue.get('html_url')}">Link</a></p>
  </body>
</html>
"""

message = MIMEMultipart("alternative")
message["Subject"] = subject
message["From"] = SENDER
message["To"] = RECEIVER
message.attach(MIMEText(html, "html"))

context = ssl.create_default_context()

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, RECEIVER, message.as_string())
        print("Email sent successfully.")
except Exception as e:
    print("Error sending email:", e)
    raise
