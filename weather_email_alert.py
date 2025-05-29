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

def get_last_n_main(n=4):
    all_rows = sheet.get_all_records(expected_headers=["🌀 Main"])
    if not all_rows:
        print("No data found in sheet")
        return []
    return all_rows[-n:]

if __name__ == "__main__":
    last_4_main = get_last_n_main(4)
    alert_needed = False

    for weather in last_4_main:
        main_condition = weather.get("🌀 Main")
        if main_condition in ["Clouds", "Rain"]:
            alert_needed = True
            break

    if alert_needed:
        subject = "🌧️ Weather Alert: Clouds or Rain Detected"
        body = "Clouds or Rain was detected in the last 4 weather updates.\nStay safe and carry an umbrella! ☔"
        send_email(subject, body, TO_EMAIL, EMAIL_USER, EMAIL_PASS)
    else:
        print("✅ No alert needed. Weather looks clear.")
