import os
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

# Authenticate with Google Sheets API using your credentials JSON file
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Open your Google Sheet by name - update the sheet name here
sheet = client.open("Cloud Weather Tracker").sheet1

def get_last_n_weather(n):
    all_rows = sheet.get_all_records(head=4)
    # Defensive: if fewer than n records exist, just return all available
    return all_rows[-n:] if len(all_rows) >= n else all_rows

def check_weather_for_alert(records):
    for record in records:
        main_condition = record.get('Main', '').lower()
        # Check if 'cloud' or 'rain' is in the weather main condition
        if 'cloud' in main_condition or 'rain' in main_condition:
            return True
    return False

def send_email_alert():
    email_user = os.environ.get('EMAIL_USER')
    email_password = os.environ.get('EMAIL_HOST_PASSWORD')
    to_email = os.environ.get('TO_EMAIL')

    if not (email_user and email_password and to_email):
        raise Exception("Email credentials or recipient email missing in environment variables.")

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = to_email
    msg['Subject'] = "Weather Alert: Clouds or Rain Detected"

    body = "The recent weather updates show clouds or rain conditions. Please take necessary precautions."
    msg.attach(MIMEText(body, 'plain'))

    # Connect to Gmail SMTP server and send email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(email_user, email_password)
        server.sendmail(email_user, to_email, msg.as_string())

if __name__ == "__main__":
    last_4_weather = get_last_n_weather(4)
    if check_weather_for_alert(last_4_weather):
        send_email_alert()
