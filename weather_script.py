import os
import base64
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import requests
import gspread
import logging
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from gspread_formatting import CellFormat, TextFormat, Color
from gspread_formatting import format_cell_range

# ✅ UTF-8 for emoji display
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Step 1: Decode the base64 Google credentials
google_credential_base64 = os.getenv('GOOGLE_SHEETS_CREDENTIALS')  # Get base64 encoded credentials from environment variable
decoded_credentials = base64.b64decode(google_credential_base64).decode('utf-8')  # Decode the base64 string

# Step 2: Convert the decoded JSON string back to a dictionary
google_credentials_json = json.loads(decoded_credentials)

# Step 3: Save the credentials to a temporary file (needed for Google API authentication)
with open('google_credential.json', 'w') as creds_file:
    json.dump(google_credentials_json, creds_file)

# 🔐 Google Sheets authentication setup
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# Step 4: Authenticate using the credentials file
creds = ServiceAccountCredentials.from_json_keyfile_name('google_credential.json', scope)
client = gspread.authorize(creds)
spreadsheet = client.open("Cloud Weather Tracker")
sheet = spreadsheet.sheet1

# 📄 Setup logging
logging.basicConfig(filename="weather_log.txt", level=logging.INFO, format='%(asctime)s - %(message)s')

class WeatherTracker:
    def __init__(self, sheet, api_key):
        self.sheet = sheet
        self.api_key = api_key
        self.units = "metric"
        self.weather_icons = {
            "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧", "Thunderstorm": "⛈",
            "Snow": "❄", "Mist": "🌫", "Drizzle": "🌦", "Haze": "🌁", "Fog": "🌁"
        }

    def deg_to_cardinal(self, deg):
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        return directions[round(deg / 45) % 8]

    def get_weather_data(self, city):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units={self.units}"
            response = requests.get(url)
            data = response.json()

            if data.get("cod") != 200:
                return None, f"API Error for {city}: {data.get('message', 'Unknown error')}"

            weather_main = data["weather"][0]["main"]
            icon = self.weather_icons.get(weather_main, "")

            sunrise = datetime.utcfromtimestamp(data["sys"]["sunrise"] + data["timezone"]).strftime('%H:%M')
            sunset = datetime.utcfromtimestamp(data["sys"]["sunset"] + data["timezone"]).strftime('%H:%M')

            weather = {
                "📅 Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "🏙️ City": data["name"],
                "🌡️ Temperature": data["main"]["temp"],
                "🌡️ Min Temp": data["main"]["temp_min"],
                "🌡️ Max Temp": data["main"]["temp_max"],
                "🥵 Feels Like": data["main"]["feels_like"],
                "💧 Humidity": data["main"]["humidity"],
                "📈 Pressure": data["main"]["pressure"],
                "💨 Wind Speed": data["wind"]["speed"],
                "🧭 Wind Dir": self.deg_to_cardinal(data["wind"]["deg"]),
                "🔭 Visibility (km)": data["visibility"] / 1000,
                "🌦️ Condition": data["weather"][0]["description"].title(),
                "🌀 Main": weather_main,
                "🖼️ Icon": icon,
                "🌅 Sunrise": sunrise,
                "🌇 Sunset": sunset
            }

            return weather, None

        except Exception as e:
            return None, f"Exception occurred for {city}: {str(e)}"

    def setup_sheet(self):
        headers = [
            "📅 Time", "🏙️ City", "🌡️ Temperature", "🌡️ Min Temp", "🌡️ Max Temp",
            "🥵 Feels Like", "💧 Humidity", "📈 Pressure", "💨 Wind Speed", "🧭 Wind Dir",
            "🔭 Visibility (km)", "🌦️ Condition", "🌀 Main", "🖼️ Icon", "🌅 Sunrise", "🌇 Sunset"
        ]
        descriptions = [
            "Log timestamp (local time)", "City name", "Current temperature (°C)",
            "Minimum temperature (°C)", "Maximum temperature (°C)", "Feels like temperature (°C)",
            "Humidity in %", "Atmospheric pressure (hPa)", "Wind speed (m/s)",
            "Wind direction (cardinal)", "Visibility in kilometers", "Weather condition description",
            "Main weather category", "Weather icon (emoji)", "Sunrise time (local)", "Sunset time (local)"
        ]

        try:
            self.sheet.batch_clear(['A1:Z3'])
            self.sheet.update('A1', [["📊 Weather Update Log"]])
            self.sheet.update('A2', [headers])
            self.sheet.update('A3', [descriptions])

            # 🎨 Formatting
            title_format = CellFormat(
                textFormat=TextFormat(bold=True, fontSize=12),
                backgroundColor=Color(0.6, 0.8, 1)
            )
            header_format = CellFormat(
                textFormat=TextFormat(bold=True, fontSize=10),
                backgroundColor=Color(0.85, 0.92, 0.97)
            )
            desc_format = CellFormat(
                textFormat=TextFormat(italic=True, fontSize=9),
                backgroundColor=Color(0.96, 0.96, 0.96)
            )

            format_cell_range(self.sheet, 'A1:Z1', title_format)
            format_cell_range(self.sheet, 'A2:Z2', header_format)
            format_cell_range(self.sheet, 'A3:Z3', desc_format)

        except Exception as e:
            print("❌ Failed to initialize sheet:", e)
            logging.error(f"Failed to initialize sheet: {e}")

    def append_weather_row(self, weather):
        try:
            headers = list(weather.keys())
            self.sheet.append_row([str(weather[k]) for k in headers])
            print(f"✅ Weather data for {weather['🏙️ City']} updated.")
            logging.info(f"✅ Weather data for {weather['🏙️ City']} updated.")
        except Exception as e:
            print(f"❌ Failed to append data for {weather['🏙️ City']}: {e}")
            logging.error(f"❌ Failed to append data for {weather['🏙️ City']}: {e}")


# 🚀 Main automation logic
if __name__ == "__main__":
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')  # Get API Key from environment

    available_cities = ["Dehradun", "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Jaipur"]

    tracker = WeatherTracker(sheet, OPENWEATHER_API_KEY)

    # ❗ Run this only once or when resetting the sheet
    # tracker.setup_sheet()

    for city in available_cities:
        weather_data, error = tracker.get_weather_data(city)
        if error:
            print("❗ Error:", error)
            logging.error(f"{city} - {error}")
        else:
            tracker.append_weather_row(weather_data)
