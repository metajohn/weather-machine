import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT = 47.62050853108323
LON = -122.34928075550654
url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print("--- 2.5 API WORKING ---")
    print(f"Location: {data['name']}")
    print(f"Temp: {data['main']['temp']}°C")
else:
    print(f"Status: {response.status_code}")
    print(f"Message: {response.text}")