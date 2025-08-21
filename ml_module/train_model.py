

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

def train_model(dataset_path='data/datasets/dataset.csv'):
    df = pd.read_csv(dataset_path)
    
    # Features
    X = df[['NumNodes', 'NodeSpeed', 'AreaSize', 'TrafficLoad', 'TxRange']]
    
    # 🎯 Target: Protocol (AODV, DSDV, OLSR)
    y = df['Protocol']
    
    # Train-test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced"
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save model with feature names
    model_data = {
        'model': model,
        'feature_names': list(X.columns)
    }
    os.makedirs('ml_module', exist_ok=True)
    joblib.dump(model_data, 'ml_module/model.pkl')
    print("✅ Model saved to ml_module/model.pkl")

if __name__ == '__main__':
    train_model()

