import joblib
import requests
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
import numpy as np

# Initialize Flask app
app = Flask(__name__)

# Load model and label encoder
try:
    model_path = "D:\Dissertation\potato_disease_prediction\saved_model\crop_disease_model_17_24.pkl"
    label_encoder_path = "D:\Dissertation\potato_disease_prediction\saved_model\label_encoder.pkl"

    loaded_model = joblib.load(model_path)
    label_encoder = joblib.load(label_encoder_path)
    print("Model and label encoder loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    loaded_model = None
    label_encoder = None

# Open Weather API configuration
weather_api_url = 'https://api.openweathermap.org/data/2.5/forecast'
api_key = 'e19337e5cb3ea6930e118761ec61b0b1'

def fetch_weather_forecast(city, country_code, days):
    """
    Fetch weather forecast for given city, country and number of days.
    """
    try:
        response = requests.get(
            weather_api_url, 
            params={
                'q': f'{city},{country_code}', 
                'appid': api_key, 
                'units': 'metric'  # Get data in Celsius
            }
        )
        
        if response.status_code != 200:
            error_msg = response.json().get('message', 'Unknown error')
            return None, f"Error fetching weather data: {error_msg}"

        forecast_data = response.json()
        
        if 'list' not in forecast_data:
            return None, "No forecast data available"
            
        weather_data = []
        daily_data = {}

        # Group forecast data by day
        for forecast in forecast_data['list']:
            date_str = forecast['dt_txt'].split(' ')[0]  # Extract date only
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

        # Sort all available forecast dates
        sorted_dates = sorted(
            daily_data.keys(),
            key=lambda d: datetime.strptime(d, '%Y-%m-%d')
        )

        # Filter starting from today (if available)
        today = datetime.now().date()
        filtered_dates = []
        for date_str in sorted_dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            if date_obj >= today:
                filtered_dates.append(date_str)
            if len(filtered_dates) == days:
                break

        # Compile daily summaries
        for date_str in filtered_dates:
            day_data = daily_data[date_str]
            weather_data.append({
                'Date': day_data['date_obj'].strftime('%d-%B-%Y'),
                'min_temp': min(day_data['temps']),
                'max_temp': max(day_data['temps']),
                'min_humidity': min(day_data['humidities']),
                'max_humidity': max(day_data['humidities']),
                'day_of_week': day_data['date_obj'].weekday(),
                'month': day_data['date_obj'].month
            })
            
        return weather_data, None

    except Exception as e:
        return None, str(e)


def predict_diseases(weather_data):
    """
    Predict diseases based on weather data
    """
    try:
        # Use the globally loaded model instead of reloading
        if loaded_model is None or label_encoder is None:
            return pd.DataFrame(), "Model or label encoder not loaded"
        
        predictions_list = []
        
        for data in weather_data:
            # Prepare feature data: [day_of_week, month, min_temp, max_temp, max_humidity, min_humidity]
            feature_data = [[
                data['day_of_week'],
                data['month'],
                data['min_temp'],
                data['max_temp'],
                data['max_humidity'],
                data['min_humidity']
            ]]

            # Make prediction
            prediction_encoded = loaded_model.predict(feature_data)[0]
            prediction = label_encoder.inverse_transform([int(prediction_encoded)])[0]
            
            predictions_list.append({
                'Date': data['Date'],
                'Predicted Disease': prediction
            })

        return pd.DataFrame(predictions_list), None
        
    except Exception as e:
        print(f"Error in predict_diseases: {e}")  # Add debug print
        return pd.DataFrame(), str(e)


# API endpoint for AJAX calls from JavaScript
@app.route('/api/predict')
def api_predict():
    city = request.args.get('city')
    country = request.args.get('country') 
    days = int(request.args.get('days', 6))
    
    if not city or not country:
        return jsonify({'error': 'City and country are required'}), 400
    
    # Use your existing functions
    weather_data, error = fetch_weather_forecast(city, country, days)
    if error:
        return jsonify({'error': error}), 400
    
    predictions, error = predict_diseases(weather_data)
    if error:
        return jsonify({'error': error}), 400
    
    # Combine data
    combined_data = []
    predictions_dict = predictions.to_dict(orient='records')
    
    for i, weather in enumerate(weather_data):
        if i < len(predictions_dict):
            combined_data.append({
                'Date': weather['Date'],
                'min_temp': weather['min_temp'],
                'max_temp': weather['max_temp'],
                'min_humidity': weather['min_humidity'],
                'max_humidity': weather['max_humidity'],
                'Predicted Disease': predictions_dict[i]['Predicted Disease']
            })
    
    return jsonify({
        'predictions': combined_data,
        'city': city,
        'country': country,
        'days': days
    })


# Traditional form submission route (for backup/compatibility)
@app.route('/live-prediction', methods=['GET', 'POST'])
def live_prediction():
    if request.method == 'POST':
        days = int(request.form.get('days', 7))  # Default to 7 days
        
        # Get city and country from form if available, otherwise use default
        city = request.form.get('city', 'Kasur')
        country = request.form.get('country', 'PK')
        
        # Use the function with city and country parameters
        weather_data, error = fetch_weather_forecast(city, country, days)
        if error:
            return render_template('live_prediction.html', error=error)
        
        predictions, error = predict_diseases(weather_data)
        if error:
            return render_template('live_prediction.html', error=error)
        
        # Combine weather data with predictions
        combined_data = []
        predictions_dict = predictions.to_dict(orient='records')
        
        for i, weather in enumerate(weather_data):
            if i < len(predictions_dict):
                combined_data.append({
                    'Date': weather['Date'],
                    'min_temp': weather['min_temp'],
                    'max_temp': weather['max_temp'],
                    'min_humidity': weather['min_humidity'],
                    'max_humidity': weather['max_humidity'],
                    'Predicted Disease': predictions_dict[i]['Predicted Disease']
                })
        
        return render_template('live_prediction.html', 
                             predictions=combined_data, 
                             days=days,
                             city=city,
                             country=country)
    
    return render_template('live_prediction.html')


if __name__ == '__main__':
    app.run(debug=True)