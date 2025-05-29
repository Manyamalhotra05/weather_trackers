import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Google Sheets setup
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
if not GOOGLE_CREDENTIALS:
    raise Exception("❌ GOOGLE_CREDENTIALS environment variable not set")

creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_CREDENTIALS), scope)
client = gspread.authorize(creds)
spreadsheet = client.open("Cloud Weather Tracker")
sheet = spreadsheet.sheet1

# Email config from environment variables
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_HOST_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

if not EMAIL_USER or not EMAIL_PASS or not TO_EMAIL:
    raise Exception("❌ EMAIL_USER, EMAIL_HOST_PASSWORD or TO_EMAIL environment variables not set")

def send_email(subject, body, to_email, email_user, email_pass):
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
        print("✅ Alert email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def get_last_n_weather(n=4):
    all_rows = sheet.get_all_records()
    if not all_rows:
        print("No data found in sheet")
        return []
    return all_rows[-n:]

if __name__ == "__main__":
    last_4_weather = get_last_n_weather(4)
    alert_needed = False
    alert_messages = []

    for weather in last_4_weather:
        main_condition = weather.get("🌀 Main")
        city = weather.get("🏙️ City")
        condition_desc = weather.get("🌦️ Condition")
        icon = weather.get("🖼️ Icon")
        temp = weather.get("🌡️ Temperature")
        humidity = weather.get("💧 Humidity")

        if main_condition in ["Clouds", "Rain"]:
            alert_needed = True
            alert_messages.append(
                f"{city}: {condition_desc} {icon}, Temp: {temp}°C, Humidity: {humidity}%"
            )

    if alert_needed:
        subject = "Weather Alert: Clouds/Rain detected in recent updates"
        body = "Weather updates with clouds or rain detected in last 4 entries:\n\n"
        body += "\n".join(alert_messages)
        body += "\n\nPlease take necessary precautions."

        send_email(subject, body, TO_EMAIL, EMAIL_USER, EMAIL_PASS)
    else:
        print("No alert needed. No Clouds or Rain in last 4 entries.")
