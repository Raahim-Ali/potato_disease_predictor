from sklearn.tree import DecisionTreeClassifier  
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import joblib
import os

def train_and_save_model():
    # Ensure directories exist
    os.makedirs('saved_model', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    os.makedirs('static/reports', exist_ok=True)

    # Load the dataset
    file_path = 'D:\Dissertation\potato_disease_prediction\data\weather_with_label_7years.csv'
    historical_data = pd.read_csv(file_path)

    # Preprocess the data
    historical_data['Date'] = pd.to_datetime(historical_data['Date'])
    historical_data['day_of_week'] = historical_data['Date'].dt.dayofweek
    historical_data['month'] = historical_data['Date'].dt.month

    # Features (X = predictors) and target variable (y = crop diseases)
    X = historical_data[['day_of_week', 'month', 'avg_temp_min', 'avg_temp_max', 'avg_humidity_max', 'avg_humidity_min']]
    y = historical_data['crop_diseases']

    # Encode the target variable
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    # Split dataset into train/test with a reproducible random state
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

    # Train Decision Tree model
    model = DecisionTreeClassifier (max_depth=3, min_samples_split=10, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate predictions
    y_pred_encoded = model.predict(X_test)

    # Decode predictions
    y_pred = label_encoder.inverse_transform(y_pred_encoded)
    y_true = label_encoder.inverse_transform(y_test)

    # Generate evaluation metrics (confusion matrix and classification report)
    conf_matrix = confusion_matrix(y_true, y_pred, labels=label_encoder.classes_)
    conf_report = classification_report(y_true, y_pred, target_names=label_encoder.classes_)

    # Print results
    print("Classification Report:\n", conf_report)
    print("Confusion Matrix:\n", conf_matrix)

    # Save classification report
    report_path = 'static/reports/classification_report.txt'
    with open(report_path, 'w') as f:
        f.write("Classification Report:\n")
        f.write(conf_report)

    # Save confusion matrix
    conf_matrix_path = 'static/images/confusion_matrix_counts.png'
    plt.figure(figsize=(8, 6))
    sns.heatmap(conf_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=label_encoder.classes_, yticklabels=label_encoder.classes_)
    plt.title("Confusion Matrix (Counts)")
    plt.xlabel("Predicted Labels")
    plt.ylabel("True Labels")
    plt.savefig(conf_matrix_path, dpi=300)
    plt.close()

    # Save normalized confusion matrix
    conf_matrix_normalized = conf_matrix.astype('float') / conf_matrix.sum(axis=1)[:, np.newaxis]
    norm_conf_matrix_path = 'static/images/confusion_matrix_normalized.png'
    plt.figure(figsize=(8, 6))
    sns.heatmap(conf_matrix_normalized, annot=True, fmt=".2f", cmap="Greens", xticklabels=label_encoder.classes_, yticklabels=label_encoder.classes_)
    plt.title("Normalized Confusion Matrix")
    plt.xlabel("Predicted Labels")
    plt.ylabel("True Labels")
    plt.savefig(norm_conf_matrix_path, dpi=300)
    plt.close()

    # Save bar chart of class wise accuracy
    accuracies = conf_matrix.diagonal() / conf_matrix.sum(axis=1)
    accuracy_chart_path = 'static/images/class_wise_accuracy.png'
    plt.figure(figsize=(8, 6))
    plt.bar(label_encoder.classes_, accuracies, color="skyblue")
    plt.title("Class-wise Accuracy")
    plt.xlabel("Classes")
    plt.ylabel("Accuracy")
    plt.ylim(0, 1)
    plt.savefig(accuracy_chart_path, dpi=300)
    plt.close()

    # Save line graph for predictions vs true counts
    pred_vs_true_path = 'static/images/predicted_vs_true_counts.png'
    plt.figure(figsize=(10, 6))
    sns.lineplot(x=label_encoder.classes_, y=np.bincount(y_pred_encoded, minlength=len(label_encoder.classes_)), label="Predicted Counts", marker="o")
    sns.lineplot(x=label_encoder.classes_, y=np.bincount(y_test, minlength=len(label_encoder.classes_)), label="True Counts", marker="o")
    plt.title("Predicted vs True Label Counts")
    plt.xlabel("Classes")
    plt.ylabel("Count")
    plt.legend()
    plt.savefig(pred_vs_true_path, dpi=300)
    plt.close()

    # Save the trained model and label encoder
    model_path = 'saved_model/crop_disease_model_17_24.pkl'
    label_encoder_path = 'saved_model/label_encoder.pkl'
    joblib.dump(model, model_path)
    joblib.dump(label_encoder, label_encoder_path)

    print("All visualizations and reports have been saved successfully.")
    return conf_matrix, report_path, [conf_matrix_path, norm_conf_matrix_path, accuracy_chart_path, pred_vs_true_path]

# Call the function to train and save the model
train_and_save_model()
