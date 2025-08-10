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
        input_data = [features[k] for k in self.feature_names]
        input_df = pd.DataFrame([input_data], columns=self.feature_names)
        
        pred_class = self.model.predict(input_df)[0]
        pred_proba = self.model.predict_proba(input_df)[0]  # array of probabilities for each class
        
        confidence = np.max(pred_proba)  # highest probability among classes
        
        protocol = self.protocol_map.get(pred_class, 'AODV')
        return protocol, confidence