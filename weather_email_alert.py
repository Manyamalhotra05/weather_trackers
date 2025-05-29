import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText

# Constants
SHEET_ID = 'YOUR_SHEET_ID'
SHEET_NAME = 'Sheet1'  # Change if your sheet name is different
EMAIL_SENDER = 'your_email@example.com'
EMAIL_PASSWORD = 'your_email_password_or_app_password'
EMAIL_RECEIVER = 'receiver_email@example.com'

# Set up Google Sheets credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

def get_last_n_weather(n):
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    # Use row 2 as header because row 1 has "weather update log"
    all_rows = sheet.get_all_records(head=2)

    return all_rows[-n:] if len(all_rows) >= n else all_rows

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

def check_and_alert():
    last_4_weather = get_last_n_weather(4)

    bad_weather_found = False
    body_lines = []

    for entry in last_4_weather:
        weather_main = entry.get("main", "")
        if weather_main in ["Clouds", "Rain"]:
            bad_weather_found = True
            line = f"{entry['time']} in {entry['city']}: {weather_main} ({entry['condition']})"
            body_lines.append(line)

    if bad_weather_found:
        subject = "⚠️ Weather Alert: Bad Weather Detected"
        body = "\n".join(body_lines)
        send_email(subject, body)
        print("Weather alert email sent.")
    else:
        print("Weather is clear. No email sent.")

if __name__ == "__main__":
    check_and_alert()
