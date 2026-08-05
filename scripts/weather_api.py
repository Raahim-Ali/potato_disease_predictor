from flask import Flask, request, jsonify
import requests
from datetime import datetime

# Initialize the Flask app
app = Flask(__name__)

# OpenWeather API key
API_KEY = "c2ea1b00bb26ecc33f7f35decf8bd5b0"
BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

def fetch_weather_data(city="Lahore", country="PK", days=5):
    """
    Fetch weather data from OpenWeather API.
    
    :city: The city for which weather data is to be fetched.
    :country: The country of the city.
    :days: The number of days of forecast data required.
    :return: A list of dictionaries containing temperature and humidity data.
    """
    try:
        # Construct API request URL for the forecast (next few days)
        url = f"{BASE_URL}?q={city},{country}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()

        if 'list' not in data:
            return []

        # Extract relevant weather data
        predictions = []
        daily_data = {}
        
        # Group data by day
        for forecast in data['list']:
            date_str = forecast['dt_txt'].split(' ')[0]  # Get just the date part from date and time in response
            temp = forecast['main']['temp']
            humidity = forecast['main']['humidity']
            
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'temps': [],
                    'humidities': [],
                    'date_obj': datetime.strptime(date_str, '%Y-%m-%d')
                }
            
            daily_data[date_str]['temps'].append(temp)
            daily_data[date_str]['humidities'].append(humidity)
        
        # Calculate daily min/max for requested days
        sorted_dates = sorted(daily_data.keys())[:days]
        
        for date_str in sorted_dates:
            day_data = daily_data[date_str]
            predictions.append({
                "date": day_data['date_obj'].strftime('%d-%B-%Y'),  # Formatted date
                "max_temp": max(day_data['temps']),
                "min_temp": min(day_data['temps']),
                "max_humidity": max(day_data['humidities']),
                "min_humidity": min(day_data['humidities'])
            })

        return predictions

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return []


@app.route('/fetch-weather-data', methods=['GET'])
def fetch_weather_data_route():
    # Get country, city, and days from request arguments
    country = request.args.get('country', 'PK')  # Default to Pakistan
    city = request.args.get('city', 'Lahore')  # Default to Lahore
    days = int(request.args.get('days', 5))  # Default to 5 days

    # Fetch the weather data
    weather_data = fetch_weather_data(city, country, days)

    if weather_data:
        # Calculate averages for backward compatibility
        if len(weather_data) > 0:
            avg_temp_max = sum(day['max_temp'] for day in weather_data) / len(weather_data)
            avg_temp_min = sum(day['min_temp'] for day in weather_data) / len(weather_data)
            avg_humidity_max = sum(day['max_humidity'] for day in weather_data) / len(weather_data)
            avg_humidity_min = sum(day['min_humidity'] for day in weather_data) / len(weather_data)
            
            return jsonify({
                "weather_data": weather_data,
                "avg_temp_max": round(avg_temp_max, 2),
                "avg_temp_min": round(avg_temp_min, 2),
                "avg_humidity_max": round(avg_humidity_max, 2),
                "avg_humidity_min": round(avg_humidity_min, 2),
                "city": city,
                "country": country,
                "days": days
            })
        else:
            return jsonify({"error": "No weather data available"}), 404
    else:
        return jsonify({"error": "Unable to fetch weather data"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)  # Using different port to avoid conflicts