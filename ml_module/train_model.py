import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

def train_model(dataset_path='data/datasets/dataset1.csv'):
    df = pd.read_csv(dataset_path)
    
    # Preprocessing
    X = df[['NumNodes', 'NodeSpeed', 'AreaSize', 'TrafficLoad', 'TxRange']]
    y = df['PerformanceClass']  # 0=Poor, 1=Fair, 2=Good, 3=Excellent
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    accuracy = model.score(X_test, y_test)
    print(f"Model accuracy: {accuracy:.2f}")
    
    # Save model with feature names
    model_data = {
        'model': model,
        'feature_names': list(X.columns)
    }
    os.makedirs('ml_module', exist_ok=True)
    joblib.dump(model_data, 'ml_module/model.pkl')
    print("Model saved to ml_module/model.pkl")

if __name__ == '__main__':
    train_model()