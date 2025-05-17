import sys
import io
import os
import json
import requests
import gspread
import logging
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from gspread_formatting import CellFormat, TextFormat, Color
from gspread_formatting import format_cell_range

# ✅ UTF-8 for emoji display
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 🔐 Google Sheets authentication setup
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# 📝 Create the credentials.json file from environment variable GOOGLE_CREDENTIALS
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
if not GOOGLE_CREDENTIALS:
    raise Exception("❌ GOOGLE_CREDENTIALS environment variable not set")

with open('credentials.json', 'w') as creds_file:
    creds_file.write(GOOGLE_CREDENTIALS)

# ❗ This line expects credentials.json to exist!
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
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
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    if not API_KEY:
        raise Exception("❌ OPENWEATHER_API_KEY environment variable not set")

    available_cities = ["Dehradun", "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Jaipur"]
    tracker = WeatherTracker(sheet, API_KEY)

    for city in available_cities:
        weather_data, error = tracker.get_weather_data(city)
        if error:
            print("❗ Error:", error)
            logging.error(f"{city} - {error}")
        else:
            tracker.append_weather_row(weather_data)
