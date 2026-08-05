from flask import Flask, render_template, request, jsonify
import joblib
import os
from scripts.input_prediction import predict_from_input
from scripts.live_prediction import fetch_weather_forecast, predict_diseases, fetch_weather_forecast
from scripts.model_training import train_and_save_model

app = Flask(__name__)

# Load trained model and Label Encoder
model_path = 'saved_model/crop_disease_model_17_24.pkl'
label_encoder_path = 'saved_model/label_encoder.pkl'

model = joblib.load(model_path)
label_encoder = joblib.load(label_encoder_path)

@app.context_processor
def inject_nav_data():
    return {
        'current_endpoint': request.endpoint
    }

# Routes 
@app.route('/')
def home():
    return render_template('home.html')  

@app.route('/live-prediction', methods=['GET', 'POST'])
def live_prediction():
    if request.method == 'POST':
        days = int(request.form.get('days', 5))  # Default to 5 days
        
        # Get city and country from form if available, otherwise use default
        city = request.form.get('city', 'Lahore')
        country = request.form.get('country', 'PK')
        
        # Use the new function with city and country parameters
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

# New API route for AJAX requests
@app.route('/api/predict', methods=['GET'])
def api_predict():
    country = request.args.get('country', 'PK')
    city = request.args.get('city', 'Lahore')
    days = int(request.args.get('days', 5))
    
    # Fetch weather data
    weather_data, weather_error = fetch_weather_forecast(city, country, days)
    
    if weather_error:
        return jsonify({"error": weather_error}), 400
    
    if not weather_data:
        return jsonify({"error": "No weather data available"}), 404
    
    # Predict diseases
    predictions_df, prediction_error = predict_diseases(weather_data)
    
    if prediction_error:
        return jsonify({"error": prediction_error}), 500
    
    # Combine weather data with predictions
    combined_data = []
    predictions_dict = predictions_df.to_dict('records')
    
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
        "predictions": combined_data,
        "city": city,
        "country": country,
        "days": days
    })

@app.route('/fetch-weather-data', methods=['GET'])
def fetch_weather_data():
    
        country = request.args.get('country', 'PK')
        city = request.args.get('city', 'Lahore')
        days = int(request.args.get('days', 5))
        
        # Fetch weather data
        weather_data, error = fetch_weather_forecast(city, country, days)
        
        if error:
            return jsonify({"error": error}), 400
        
        if not weather_data:
            return jsonify({"error": "No data found for the selected location."}), 404
        
        # Calculate averages for JavaScript compatibility
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

@app.route('/input-prediction', methods=['GET', 'POST'])
def input_prediction():
    prediction = None  # Default state
    error = None  # Error message placeholder
    weather_data = None  # To store fetched weather data for form filling

    if request.method == 'POST':
        try:
            # Collect input data from the form
            max_temp = float(request.form['avg_temp_max'])
            min_temp = float(request.form['avg_temp_min'])
            max_humidity = float(request.form['avg_humidity_max'])
            min_humidity = float(request.form['avg_humidity_min'])

            # Prepare input data for prediction
            input_data = [max_temp, min_temp, max_humidity, min_humidity]

            # Predict using the model
            prediction = predict_from_input(input_data, model_path, label_encoder_path)

        except ValueError:
            error = "Invalid input values. Please ensure all fields are filled correctly."
        except Exception as e:
            error = f"An error occurred: {str(e)}"

    # Render the template with the prediction or error message
    return render_template('input_prediction.html', prediction=prediction, error=error, weather_data=weather_data)


def get_existing_training_files():
    """Get existing training files from static folders"""
    try:
        # Define expected file paths (without timestamps)
        expected_files = {
            'images': {
                'confusion_matrix_counts': 'static/images/confusion_matrix_counts.png',
                'confusion_matrix_normalized': 'static/images/confusion_matrix_normalized.png', 
                'class_wise_accuracy': 'static/images/class_wise_accuracy.png',
                'predicted_vs_true_counts': 'static/images/predicted_vs_true_counts.png'
            },
            'report': 'static/reports/classification_report.txt'
        }
        
        # Check files exist
        existing_images = {}
        for key, path in expected_files['images'].items():
            if os.path.exists(path):
                existing_images[key] = os.path.basename(path)
        
        # Check if report exists
        report_exists = os.path.exists(expected_files['report'])
        report_file = 'classification_report.txt' if report_exists else None
        
        return {
            'images': existing_images,
            'report_file': report_file,
            'has_results': len(existing_images) > 0 or report_exists
        }
        
    except Exception as e:
        print(f"Error checking training files: {str(e)}")
        return {
            'images': {},
            'report_file': None,
            'has_results': False
        }
    
@app.route('/visuals', methods=['GET'])
def model_training():
    """Display existing training results"""
    
    # Get existing training files
    training_files = get_existing_training_files()
    
    if training_files['has_results']:
        return render_template(
            'visuals.html',
            images=training_files['images'],
            report_file=training_files['report_file'],
            success=True,
            message="Displaying training results from your VS Code training session."
        )
    else:
        return render_template(
            'visuals.html',
            success=False,
            message="No training results found. Please run model_training.py in VS Code first to generate visualizations."
        )

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    # Ensure saved_model and static directories exist
    os.makedirs('saved_model', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    os.makedirs('static/reports', exist_ok=True)

    app.run(debug=True)