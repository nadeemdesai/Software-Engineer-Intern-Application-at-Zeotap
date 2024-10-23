import urllib.request
import json
from datetime import datetime
from collections import Counter

# Constants
API_KEY = "4ba653b1d5b71e405301a714629d8f5f"  # Replace with your actual API key
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
CITIES = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]

def kelvin_to_celsius(kelvin):
    return kelvin - 273.15

def get_weather_data(city):
    url = f"{BASE_URL}?q={city}&appid={API_KEY}"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return {
                "city": city,
                "main": data["weather"][0]["main"],
                "temp": kelvin_to_celsius(data["main"]["temp"]),
                "feels_like": kelvin_to_celsius(data["main"]["feels_like"]),
                "dt": datetime.fromtimestamp(data["dt"]).strftime('%Y-%m-%d %H:%M:%S')
            }
    except urllib.error.HTTPError as e:
        print(f"Error fetching data for {city}: {e.code}")
        return None
    except Exception as e:
        print(f"An error occurred while fetching data for {city}: {str(e)}")
        return None

def check_alert_thresholds(data, threshold=35):
    if data["temp"] > threshold:
        print(f"ALERT: Temperature in {data['city']} exceeds {threshold}°C!")

def simulate_daily_summary(data_list):
    print("\nSimulated Daily Summary:")
    for city in CITIES:
        city_data = [d for d in data_list if d["city"] == city]
        if city_data:
            temps = [d["temp"] for d in city_data]
            conditions = [d["main"] for d in city_data]
            avg_temp = sum(temps) / len(temps)
            max_temp = max(temps)
            min_temp = min(temps)
            dominant_condition = Counter(conditions).most_common(1)[0][0]
            
            print(f"{city}:")
            print(f"  Average Temperature: {avg_temp:.2f}°C")
            print(f"  Maximum Temperature: {max_temp:.2f}°C")
            print(f"  Minimum Temperature: {min_temp:.2f}°C")
            print(f"  Dominant Condition: {dominant_condition}")
            print()

def main():
    all_data = []
    for city in CITIES:
        data = get_weather_data(city)
        if data:
            all_data.append(data)
            print(f"Weather in {data['city']}:")
            print(f"  Condition: {data['main']}")
            print(f"  Temperature: {data['temp']:.2f}°C")
            print(f"  Feels Like: {data['feels_like']:.2f}°C")
            print(f"  Time: {data['dt']}")
            print()
            check_alert_thresholds(data)
    
    simulate_daily_summary(all_data)

if __name__ == "__main__":
    main()
