# from flask import Flask, render_template, jsonify, request
# from flask_socketio import SocketIO
# from simulation_engine.simulator import MANETSimulator
# from ml_module.predictor import ProtocolPredictor
# import threading
# import os
# import json
# import time
# from simulation_engine.config import stop_simulation,reset

# app = Flask(__name__)
# socketio = SocketIO(app)
# simulator = None
# sim_thread = None
# predictor = ProtocolPredictor('ml_module/model.pkl')

# # Add at the top of the file
# simulator = None
# sim_thread = None

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/start_simulation', methods=['POST'])
# def start_simulation():
#     global simulator, sim_thread
#     config = request.json

#     # Reset stop flag
#     reset()
    
#     # Stop existing simulation if running
#     if simulator and sim_thread and sim_thread.is_alive():
#         stop_simulation = True
#         sim_thread.join(timeout=1.0)
    
#     # Use areaSize parameter
#     area_size_val = config.get('areaSize', 1000)
#     area_size = (area_size_val, area_size_val)
    
#     # Initialize new simulation
#     simulator = MANETSimulator(
#         num_nodes=config['numNodes'],
#         area_size=area_size,
#         protocol=config['protocol'],
#         sim_time=config['simTime'],
#         traffic_load=config.get('trafficLoad', 10),
#         node_speed=config.get('nodeSpeed', 5),
#         tx_range=config.get('txRange', 100),
#         pause_time=config.get('pauseTime', 2)
#     )
    
#     # Start simulation in background thread
#     sim_thread = threading.Thread(target=run_simulation, args=(socketio, simulator))
#     sim_thread.daemon = True
#     sim_thread.start()
    
#     return jsonify({"status": "started"})

# def run_simulation(sio, sim):
#     try:
#         for event in sim.run():
#             if stop_simulation:
#                 print("Simulation stopped by user")
#                 sio.emit('sim_stopped', {'message': 'Simulation stopped by user'})
#                 return
                
#             sio.emit('sim_update', event)
#             if event.get('type') == 'final_metrics':
#                 sio.emit('sim_complete', event)
#     except Exception as e:
#         print(f"Simulation error: {str(e)}")
#         sio.emit('sim_error', {'error': str(e)})

# @app.route('/stop_simulation', methods=['POST'])
# def stop_simulation_route():
#     from simulation_engine import config
#     config.stop_simulation = True
#     return jsonify({"status": "stopping"})


# @app.route('/predict_protocol', methods=['POST'])
# def predict_protocol():
#     params = request.json
#     prediction = predictor.predict({
#         'NumNodes': params['numNodes'],
#         'NodeSpeed': params['nodeSpeed'],
#         'AreaSize': params['areaSize'],
#         'TrafficLoad': params['trafficLoad'],
#         'TxRange': params['txRange']
#     })
#     return jsonify({"protocol": prediction})

# @app.route('/get_history')
# def get_history():
#     simulations = []
#     sim_dir = 'data/simulations'
#     if not os.path.exists(sim_dir):
#         os.makedirs(sim_dir, exist_ok=True)
#     for file in os.listdir(sim_dir):
#         if file.endswith('.json'):
#             with open(os.path.join(sim_dir, file)) as f:
#                 try:
#                     simulations.append(json.load(f))
#                 except:
#                     pass
#     return jsonify(simulations)

# if __name__ == '__main__':
#     os.makedirs('data/simulations', exist_ok=True)
#     socketio.run(app, debug=True)



# app.py

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from simulation_engine.simulator import MANETSimulator
from ml_module.predictor import ProtocolPredictor
import threading
import os
import json
import time
from simulation_engine import config  # use the module to set flags

app = Flask(__name__)
socketio = SocketIO(app)
simulator = None
sim_thread = None
predictor = ProtocolPredictor('ml_module/model.pkl')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    global simulator, sim_thread
    config.reset()
    cfg = request.json

    # Stop existing simulation if running
    if simulator and sim_thread and sim_thread.is_alive():
        config.set_stop()
        sim_thread.join(timeout=1.0)

    # Use areaSize parameter
    area_size_val = cfg.get('areaSize', 1000)
    area_size = (area_size_val, area_size_val)

    # Initialize simulator
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

    # Start background thread to iterate simulator.run() and emit via socketio
    def _bg():
        try:
            for event in simulator.run():
                # Check shared stop flag
                if config.get_stop():
                    print("Simulation stopped by user")
                    socketio.emit('sim_stopped', {'message': 'Simulation stopped by user'})
                    return

                socketio.emit('sim_update', event)
                if event.get('type') == 'final_metrics':
                    socketio.emit('sim_complete', event)
        except Exception as e:
            print("Simulation error:", str(e))
            socketio.emit('sim_error', {'error': str(e)})

    sim_thread = threading.Thread(target=_bg, daemon=True)
    sim_thread.start()

    return jsonify({"status": "started"})

@app.route('/stop_simulation', methods=['POST'])
def stop_simulation_route():
    # Properly set the shared flag via the config module
    config.set_stop()
    return jsonify({"status": "stopping"})

@app.route('/predict_protocol', methods=['POST'])
def predict_protocol():
    params = request.json
    prediction = predictor.predict({
        'NumNodes': params['numNodes'],
        'NodeSpeed': params['nodeSpeed'],
        'AreaSize': params['areaSize'],
        'TrafficLoad': params['trafficLoad'],
        'TxRange': params['txRange']
    })
    return jsonify({"protocol": prediction})

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
