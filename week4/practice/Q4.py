import requests

API_KEY = "b6d81b1446ede1c7a6a1e662785e9559"   # replace with your key
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_weather(city):
    url = f"{BASE_URL}?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        city_name = data["name"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        condition = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        print(f"\n🌍 Weather in {city_name}:")
        print(f"🌡️ Temperature: {temp}°C (Feels like {feels_like}°C)")
        print(f"☁️ Condition: {condition}")
        print(f"💧 Humidity: {humidity}%")
        print(f"🌬️ Wind Speed: {wind_speed} m/s")

        # Optional: check if rain data exists
        if "rain" in data:
            print(f"🌧️ Rain (last 1h): {data['rain'].get('1h', 0)} mm")
    else:
        print("❌ Error:", data.get("message", "City not found"))

# ------------------ Usage ------------------
city = input("Enter city name (e.g., Mumbai,IN): ")
get_weather(city)
