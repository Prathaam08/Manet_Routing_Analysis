# ml_model/trainer.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# --- 1. Load The Dataset ---
# Construct the path to the dataset file
dataset_path = os.path.join(os.path.dirname(__file__), 'dataset.csv')

try:
    df = pd.read_csv(dataset_path)
    print("Dataset loaded successfully!")
    print("Dataset preview:")
    print(df.head())
except FileNotFoundError:
    print(f"Error: dataset.csv not found at {dataset_path}")
    print("Please make sure the dataset.csv file is in the 'ml_model' directory.")
    exit()

# --- 2. Prepare Data for Training ---
# Define the features (X) and the target (y)
# We now include all relevant features for a more accurate model.
features = ['num_nodes', 'area_size', 'mobility', 'traffic_load', 'energy_consumption']
target = 'best_protocol'

X = df[features]
y = df[target]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

print("\nTraining data shape:", X_train.shape)
print("Testing data shape:", X_test.shape)

# --- 3. Train the Random Forest Model ---
# We use a RandomForestClassifier, which is excellent for this type of task.
model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
model.fit(X_train, y_train)
print("\nModel training complete.")

# --- 4. Evaluate the Model's Performance ---
predictions = model.predict(X_test)

# Calculate accuracy
accuracy = accuracy_score(y_test, predictions)
print(f"\nModel Accuracy: {accuracy:.2%}")

# Show a detailed classification report
print("\nClassification Report:")
print(classification_report(y_test, predictions, target_names=['AODV', 'DSDV', 'DSR']))

# --- 5. Save the Trained Model ---
model_save_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
joblib.dump(model, model_save_path)
print(f"\nModel successfully saved to {model_save_path}")