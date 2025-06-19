import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Google Sheets API scope
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

print("Authenticating with Google Sheets...")

# Authenticate with Google Sheets API using your credentials JSON file
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    print("Google Sheets authentication successful.")
except Exception as e:
    print("Failed to authenticate with Google Sheets.")
    print(e)
    exit(1)

# Open your Google Sheet by name
try:
    sheet = client.open("Cloud Weather Tracker").sheet1
    print("Opened Google Sheet successfully.")
except Exception as e:
    print("Failed to open Google Sheet.")
    print(e)
    exit(1)

def get_last_n_weather(n):
    try:
        all_rows = sheet.get_all_records(head=2)
        print(f"Retrieved {len(all_rows)} rows from sheet.")
        return all_rows[-n:] if len(all_rows) >= n else all_rows
    except Exception as e:
        print("Error while fetching weather data.")
        print(e)
        return []

def check_weather_for_alert(records):
    print("Checking weather conditions...")
    for record in records:
        main_condition = record.get('Main', '').lower()
        print(f"Found weather condition: {main_condition}")
        if 'cloud' in main_condition or 'rain' in main_condition:
            print("Alert: Clouds or rain detected.")
            return True
    print("No alert conditions found.")
    return False

def send_email_alert():
    print("Preparing to send email alert...")

    email_user = os.environ.get('EMAIL_USER')
    email_password = os.environ.get('EMAIL_HOST_PASSWORD')
    to_email = os.environ.get('TO_EMAIL')

    if not (email_user and email_password and to_email):
        print("Missing email credentials or recipient email in environment variables.")
        return

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = to_email
    msg['Subject'] = "Weather Alert: Clouds or Rain Detected"

    body = "The recent weather updates show clouds or rain conditions. Please take necessary precautions."
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.sendmail(email_user, to_email, msg.as_string())
        print("Email alert sent successfully.")
    except Exception as e:
        print("Failed to send email alert.")
        print(e)

# Main workflow
if __name__ == "__main__":
    print("Starting weather alert check...")

    last_4_weather = get_last_n_weather(4)
    if not last_4_weather:
        print("No weather data available to check.")
        exit(0)

    if check_weather_for_alert(last_4_weather):
        send_email_alert()
    else:
        print("No email sent. Weather is clear.")
