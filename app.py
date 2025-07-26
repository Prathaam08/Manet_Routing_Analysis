from flask import Flask, render_template, request, jsonify
from simulation.simulator import run_simulation
from ml_model.predictor import predict_protocol
import os

app = Flask(__name__)

# Ensure a directory for saving plots exists
if not os.path.exists('static/results'):
    os.makedirs('static/results')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    params = request.get_json()
    
    # --- ML Prediction Step ---
    # ✅ Get all 5 features directly from the GUI request
    features = [
        int(params.get('num_nodes')),
        int(params.get('area')),
        int(params.get('mobility')),
        int(params.get('traffic_load')),
        int(params.get('energy'))
    ]
    predicted_protocol = predict_protocol(features)

    # --- Simulation Step ---
    # Extract parameters needed for the simulation function
    num_nodes = int(params.get('num_nodes'))
    area = int(params.get('area'))
    sim_time = int(params.get('sim_time'))
    protocol_choice = params.get('protocol')
    
    if protocol_choice == 'ml_predict':
        protocols_to_run = [predicted_protocol]
    elif protocol_choice == 'all':
        protocols_to_run = ['AODV', 'DSDV', 'DSR']
    else:
        protocols_to_run = [protocol_choice]

    results = {}
    for proto in protocols_to_run:
        metrics, plot_path = run_simulation(num_nodes, (area, area), sim_time, proto)
        results[proto] = {'metrics': metrics, 'plot_path': plot_path}

    return jsonify({
        'predicted_protocol': predicted_protocol,
        'simulation_results': results
    })

if __name__ == '__main__':
    app.run(debug=True)