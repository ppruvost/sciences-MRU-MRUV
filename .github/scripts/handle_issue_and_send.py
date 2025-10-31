#!/usr/bin/env python3
import json
import os
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Lecture du payload d'event GitHub
event_path = os.environ.get("GITHUB_EVENT_PATH", "/github/workflow/event.json")
with open(event_path, "r", encoding="utf-8") as f:
    event = json.load(f)

issue = event.get("issue", {})
title = issue.get("title", "")
body = issue.get("body", "")

# Extraire les informations depuis le corps de l'issue (on suppose un format simple)
# Exemple de corps attendu:
# Nom: Dupont
# Prénom: Paul
# Score: 15 / 20
# Timestamp: 2025-10-31T12:34:56Z

def parse_field(text, field_name):
    for line in text.splitlines():
        if line.strip().lower().startswith(field_name.lower() + ":"):
            return line.split(":",1)[1].strip()
    return ""

nom = parse_field(body, "Nom")
prenom = parse_field(body, "Prénom")
score = parse_field(body, "Score")
timestamp = parse_field(body, "Timestamp")
if not timestamp:
    timestamp = datetime.utcnow().isoformat() + "Z"

# Variables d'environnement secrètes
SENDER = os.environ.get("EMAIL_USER")
PASSWORD = os.environ.get("EMAIL_PASS")
RECEIVER = os.environ.get("RECEIVER_EMAIL")

if not all([SENDER, PASSWORD, RECEIVER]):
    print("ERROR: EMAIL_USER, EMAIL_PASS et RECEIVER_EMAIL doivent être définis dans les secrets.")
    raise SystemExit(1)

subject = f"Résultats du quiz — {prenom} {nom} — {score}"

html = f"""
<html>
  <body>
    <h2>Résultats du quiz</h2>
    <p><strong>Nom :</strong> {nom}</p>
    <p><strong>Prénom :</strong> {prenom}</p>
    <p><strong>Score :</strong> {score}</p>
    <p><strong>Horodatage :</strong> {timestamp}</p>
    <hr>
    <p>Issue GitHub: {issue.get('html_url')}</p>
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
    print("Email envoyé avec succès.")
except Exception as e:
    print("Erreur lors de l'envoi de l'email :", e)
    raise
