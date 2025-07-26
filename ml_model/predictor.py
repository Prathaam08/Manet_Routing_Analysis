import joblib
import numpy as np
import pandas as pd # Import pandas
import os

# Load the trained model
try:
    model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
    model = joblib.load(model_path)
    protocol_map = {0: 'AODV', 1: 'DSDV', 2: 'DSR'}
except FileNotFoundError:
    model = None
    print("Warning: ML model not found. Run trainer.py to generate it.")

def predict_protocol(features_list):
    """Predicts the best protocol based on network features."""
    if model is None:
        return "N/A (Model not loaded)"
        
    # The input 'features_list' should be a list like [num_nodes, area_size, mobility, etc.]
    # ✅ FIX: Use a DataFrame to preserve feature names and prevent warnings.
    feature_names = ['num_nodes', 'area_size', 'mobility', 'traffic_load', 'energy_consumption']
    features_df = pd.DataFrame([features_list], columns=feature_names)
    
    prediction = model.predict(features_df)
    return protocol_map[prediction[0]]