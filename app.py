# app.py
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from simulation_engine.simulator import MANETSimulator
from ml_module.predictor import ProtocolPredictor
import threading
import os
import json
import time
from uuid import uuid4
from simulation_engine import config  # use the module to set flags

app = Flask(__name__)
socketio = SocketIO(app)
simulator = None
sim_thread = None
current_run_id = None
predictor = ProtocolPredictor('ml_module/model.pkl')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    global simulator, sim_thread, current_run_id
    cfg = request.json or {}
    print("Received JSON:", cfg)

    # Generate a new run id for this run
    run_id = str(uuid4())
    current_run_id = run_id  # module-level variable (create at top: current_run_id = None)

    # Stop existing simulation if running
    if simulator and sim_thread and sim_thread.is_alive():
        print("Stopping previous simulation...")
        config.set_stop()

        # Also try to set node-level stop_flag for faster exit
        try:
            for n in getattr(simulator, 'nodes', []):
                try:
                    n.simulator.stop_flag = True
                except Exception:
                    pass
        except Exception:
            pass

        # wait up to 3 seconds for the thread to exit
        wait_start = time.time()
        while sim_thread.is_alive() and (time.time() - wait_start) < 3.0:
            time.sleep(0.05)

        if sim_thread.is_alive():
            print("Warning: previous simulation thread still alive after timeout. Continuing with new run.")

    # Now create the new simulator using provided params (fall back to defaults)
    area_size_val = cfg.get('areaSize', 1000)
    area_size = (area_size_val, area_size_val)

    simulator = MANETSimulator(
        num_nodes=cfg.get('numNodes', 50),
        area_size=area_size,
        protocol=cfg.get('protocol', 'AODV'),
        sim_time=cfg.get('simTime', 60),
        traffic_load=cfg.get('trafficLoad', 10),
        node_speed=cfg.get('nodeSpeed', 5),
        tx_range=cfg.get('txRange', 100),
        pause_time=cfg.get('pauseTime', 2)
    )

    # background thread iterates the generator and emits events with run_id
    def _bg(local_run_id):
        try:
            for event in simulator.run():
                # If someone requested stop for this run id, exit
                if config.get_stop():
                    print(f"[{local_run_id}] Simulation stopped by user")
                    socketio.emit('sim_stopped', {'message': 'Simulation stopped by user', 'run_id': local_run_id})
                    return

                # attach run_id to event so frontend can filter out-of-date events
                if isinstance(event, dict):
                    event['run_id'] = local_run_id

                socketio.emit('sim_update', event)
                if event.get('type') == 'final_metrics':
                    socketio.emit('sim_complete', dict(event, run_id=local_run_id))
        except Exception as e:
            print(f"[{local_run_id}] Simulation error:", str(e))
            socketio.emit('sim_error', {'error': str(e), 'run_id': local_run_id})

    sim_thread = threading.Thread(target=_bg, args=(run_id,), daemon=True)
    sim_thread.start()

    return jsonify({"status": "started", "run_id": run_id})

@app.route('/stop_simulation', methods=['POST'])
def stop_simulation_route():
    # Properly set the shared flag via the config module
    config.set_stop()
    return jsonify({"status": "stopping"})

@app.route('/predict_protocol', methods=['POST'])
def predict_protocol():
    params = request.json
    prediction,confidence = predictor.predict({
        'NumNodes': params['numNodes'],
        'NodeSpeed': params['nodeSpeed'],
        'AreaSize': params['areaSize'],
        'TrafficLoad': params['trafficLoad'],
        'TxRange': params['txRange']
    })
    return jsonify({"protocol": prediction,
                     "confidence": round(confidence, 3) })

@app.route('/get_history')
def get_history():
    simulations = []
    sim_dir = 'data/simulations'
    if not os.path.exists(sim_dir):
        os.makedirs(sim_dir, exist_ok=True)
    for file in os.listdir(sim_dir):
        if file.endswith('.json'):
            with open(os.path.join(sim_dir, file)) as f:
                try:
                    simulations.append(json.load(f))
                except:
                    pass
    return jsonify(simulations)

if __name__ == '__main__':
    os.makedirs('data/simulations', exist_ok=True)
    socketio.run(app, debug=True)
