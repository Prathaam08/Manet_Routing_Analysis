# Simulation and Performance Analysis of MANET Routing Protocols with GUI and ML Support

## 1. Project Overview
This project presents a comprehensive, web-based Graphical User Interface (GUI) tool designed for the simulation and performance analysis of Mobile Ad-hoc Network (MANET) routing protocols. It evaluates and compares key protocols like **AODV**, **DSDV**, and **DSR**.

A standout feature is the **Machine Learning** model that predicts the optimal routing protocol based on parameters like node density, mobility, and traffic load. This intelligent layer enhances decision-making before simulation.

This tool is ideal for students, researchers, and network engineers seeking an accessible platform to explore MANET routing strategies without diving into complex simulation coding.

---

## 2. Key Features
- 🎛️ **Interactive Web GUI** using HTML and Bootstrap.
- 📡 **Protocol Simulation** for AODV, DSDV, and DSR.
- 🤖 **Machine Learning Prediction** using a Random Forest Classifier.
- 📊 **Performance Metrics**:
  - Packet Delivery Ratio (PDR)
  - Average End-to-End Delay
  - Throughput
  - Energy Consumption
- 🧭 **Data Visualization** of network topology.
- ⚖️ **Comparative Analysis** across all protocols in a single view.

---

## 3. System Architecture & Technology Stack

| Component         | Technology                      | Purpose                                           |
|------------------|----------------------------------|---------------------------------------------------|
| Web Framework     | Flask                            | Backend API server                                |
| Frontend          | HTML, CSS, JavaScript, Bootstrap | Web-based user interface                          |
| Simulation Engine | SimPy, NetworkX                  | Discrete-event simulation and topology management |
| ML Module         | Scikit-learn, Pandas, Joblib     | Prediction of best protocol                       |
| Visualization     | Matplotlib                       | Network topology plotting                         |

---

## 4. Project Structure

```
MANET_Simulation_Tool/
├── app.py                      # Main Flask application
├── requirements.txt            # Project dependencies
├── README.md                   # Project documentation
│
├── simulation/
│   ├── simulator.py            # Core simulation logic (SimPy)
│   ├── network_env.py          # NetworkX-based topology manager
│   └── protocols/
│       ├── base_protocol.py    # Abstract base class
│       ├── aodv.py             # AODV implementation
│       ├── dsdv.py             # DSDV implementation
│       └── dsr.py              # DSR implementation
│
├── ml_model/
│   ├── trainer.py              # Training script
│   ├── predictor.py            # Prediction handler
│   ├── model.pkl               # Trained ML model
│   └── dataset.csv             # Dataset for training
│
├── templates/
│   └── index.html              # Main GUI interface
│
└── static/
    ├── css/
    │   └── style.css           # Custom styles
    └── js/
        └── main.js             # JS logic and fetch API calls
```

---

## 5. Setup and Installation

### 🔧 Prerequisites
- Python 3.8+
- `pip` and `venv`

### ⚙️ Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Prathaam08/Manet_Routing_Analysis.git
   cd Manet_Routing_Analysis
   ```

2. **Create Virtual Environment**
   - **Windows**:
     ```bash
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) Retrain the ML Model**
   ```bash
   python ml_model/trainer.py
   ```

5. **Run the Flask App**
   ```bash
   flask run
   ```

Access the app at: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 6. How to Use the Application

1. **Navigate to the GUI** in your browser.

2. **Set Simulation Parameters**:
   - Number of Nodes
   - Area Size (m x m)
   - Simulation Time (s)
   - Mobility Speed
   - Traffic Load
   - Energy Budget

3. **Choose Protocol Mode**:
   - 🤖 **Auto-Select** (via ML Prediction)
   - 🚀 **Manual Selection** (AODV, DSDV, DSR)
   - ⚖️ **Compare All**

4. **Run Simulation**: Click **Run Simulation**.

5. **View Results**:
   - ML recommendation
   - Performance metric cards (PDR, Delay, Throughput, Energy)
   - Network topology visualization

---

## 7. Advanced: Dataset Generation via NS-3

For high-fidelity datasets, you can use NS-3:

### 📄 Components
- `manet-simulation.cc`: C++ script for NS-3 simulation.
- `run_simulations.sh`: Automates multiple NS-3 runs with varying params.
- `create_ml_dataset.py`: Converts NS-3 results into labeled ML training data.

This process generates `dataset.csv` based on realistic protocol behavior.

---

## 8. Conclusion & Future Work

This project effectively demonstrates the **performance comparison** of MANET routing protocols and adds an **intelligent ML layer** for prediction.

### 🛠️ Future Enhancements
- Add protocols: OLSR, ZRP, etc.
- Advanced mobility models (Random Waypoint, Gauss-Markov).
- Real-time animation of network dynamics.
- More metrics: jitter, hop count, routing overhead.
- Deploy to cloud (Heroku, AWS) for public access.

---

## 📫 Contact

For any queries or contributions, feel free to open an issue or fork the repository.

Happy Simulating! 🚀
