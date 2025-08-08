# simulation_engine/config.py

# Global flag to control simulation execution
stop_simulation = False

def reset():
    global stop_simulation
    stop_simulation = False