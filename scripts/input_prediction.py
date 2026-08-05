import numpy as np
import joblib
import pandas as pd


def predict_from_input(input_data, model_path, encoder_path):
    """
    Disease prediction based on user provided input data using the trained model.

    input_data: List of input features [max_temp, min_temp, max_humidity, min_humidity].
    model_path: Path to the saved trained model.
    encoder_path: Path to the saved label encoder.
    return: Prediction label.
    """
    try:
        # Load the trained model
        model = joblib.load(model_path)

        # Load the label encoder
        label_encoder = joblib.load(encoder_path)

        # Ensure input_data has exactly 4 features
        if len(input_data) != 4:
            raise ValueError(f"Expected 4 input features, but got {len(input_data)} features.")

        # Default features
        day_of_week = 0  # Default: Sunday
        month = 1        # Default: January
        avg_temp_max = input_data[0]  # input data for avg_temp_max
        avg_temp_min = input_data[1]  # input data for avg_temp_min
        avg_humidity_max = input_data[2]  # input data for avg_humidity_max
        avg_humidity_min = input_data[3]  # input data for avg_humidity_min

        # Prepare input data with the required 6 features
        extended_input_data = [day_of_week, month, avg_temp_min, avg_temp_max,  avg_humidity_max, avg_humidity_min]

        # Convert input data to DataFrame (rows and coloumns)
        feature_columns = ["day_of_week", "month", "avg_temp_min", "avg_temp_max",  "avg_humidity_max", "avg_humidity_min"]
        input_df = pd.DataFrame([extended_input_data], columns=feature_columns)

        # Model makes a prediction based on data frame and selects the first value from array (the only prediction)
        prediction_encoded = model.predict(input_df)[0]  # Single prediction

        # Decode the numerical prediction into human readable form
        prediction_label = label_encoder.inverse_transform([int(prediction_encoded)])[0]

        return prediction_label
    except Exception as e:
        print(f"Error during input prediction: {e}")
        return "Prediction Error"
