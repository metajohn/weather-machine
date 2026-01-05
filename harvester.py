import os
import requests
from dotenv import load_dotenv
import sqlite3

def init_db():
#    """Creates db file and table if they don't exist"""
    conn = sqlite3.connect("weather_data.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seattle_weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATEMTIME DEFAULT CURRENT_TIMESTAMP,
            temp_c REAL7,
            humidity_pct INTEGER,
            wind_speed_ms REAL,
            description TEXT
        )
    ''')

    #save db
    conn.commit()
    #close db
    conn.close()

    print("Database check: Table is ready.")

if __name__ == "__main__":
    init_db()

#load the .env as an environment variable
load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

#This is a test location, currently the space needle
LAT = 47.62050853108323
LON = -122.34928075550654

#Create the url from the relevant parts, currently latitude, longitude, and the api key
url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"


response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    #Extraction
    temp = data['main']['temp']
    humid = data ['main']['humidity']
    wind = data['wind']['speed']
    desc = data['weather'][0]['description']

    #Connection
    conn = sqlite3.connect("weather_data.db")
    cursor = conn.cursor()

    #Execution
    cursor.execute('''
        INSERT INTO seattle_weather (temp_c, humidity_pct, wind_speed_ms, description)
        VALUES (?, ?, ?, ?)
    ''', (temp, humid, wind, desc))

    conn.commit()
    conn.close()
    print("Weather Recorded in Database")
    print(f"Weather:\nTemperature: {temp}°C\nHumidity: {humid}\nWind Speed: {wind}\nDescription: {desc}")
else:
    print(f"Status: {response.status_code}")
    print(f"Message: {response.text}")