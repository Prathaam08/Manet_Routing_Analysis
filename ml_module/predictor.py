import joblib
import numpy as np
import pandas as pd

class ProtocolPredictor:
    def __init__(self, model_path):
        model_data = joblib.load(model_path)
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.protocol_map = {
            0: 'AODV',
            1: 'DSDV',
            2: 'DSR',
            3: 'OLSR'
        }
    
    def predict(self, features):
        # Create input in correct order
        input_data = [features[k] for k in self.feature_names]
        input_df = pd.DataFrame([input_data], columns=self.feature_names)
        prediction = self.model.predict(input_df)[0]
        return self.protocol_map.get(prediction, 'AODV')