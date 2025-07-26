# simulation/simulator.py
import simpy
import random
import matplotlib

# Must be set BEFORE importing pyplot
matplotlib.use('Agg')  # ✅ Add this line!

import matplotlib.pyplot as plt
import networkx as nx       # Make sure networkx is imported here
from .network_env import NetworkEnvironment
# Import your protocol classes
from .protocols.aodv import AODV
from .protocols.dsdv import DSDV
from .protocols.dsr import DSR

# ... rest of your simulator code

def run_simulation(num_nodes, area, sim_time, protocol_name):
    """Configures and runs a single simulation."""
    env = simpy.Environment()
    network_env = NetworkEnvironment(env, area)
    
    # Create nodes and assign protocols
    nodes = []
    protocol_class = {'AODV': AODV, 'DSDV': DSDV, 'DSR': DSR}[protocol_name]
    for i in range(num_nodes):
        node = protocol_class(env, f"Node-{i}", network_env)
        nodes.append(node)
        network_env.add_node(node)
        
    # TODO: Add simulation logic here (e.g., packet generation, node movement)
    # env.process(generate_traffic(env, nodes))
    # env.process(move_nodes(env, nodes, network_env))

    env.run(until=sim_time)
    
    # --- Performance Metrics Calculation ---
    # TODO: Collect data during simulation and calculate these metrics
    packet_delivery_ratio = random.uniform(0.85, 0.98) # Placeholder
    throughput = random.uniform(150, 250) # Placeholder in kbps
    avg_end_to_end_delay = random.uniform(50, 150) # Placeholder in ms
    
    metrics = {
        'Packet Delivery Ratio': f"{packet_delivery_ratio:.2%}",
        'Throughput (kbps)': f"{throughput:.2f}",
        'Avg End-to-End Delay (ms)': f"{avg_end_to_end_delay:.2f}"
    }
    
    # --- Data Visualization ---
    # Example: Plotting nodes
     
    # Get the dictionary of node positions
    positions = network_env.get_full_positions_dict()
    
    fig, ax = plt.subplots()
    # Draw the network graph
    nx.draw(network_env.graph, pos=positions, ax=ax, with_labels=True, node_size=200, node_color='skyblue', font_size=8)
    
    ax.set_title(f"Network Topology for {protocol_name}")
    # Set limits based on area to ensure consistent plot scales
    ax.set_xlim(0, area[0])
    ax.set_ylim(0, area[1])
    # Turn off the axes for a cleaner look
    ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)

    plot_path = f"static/results/{protocol_name}_topology.png"
    plt.savefig(plot_path, bbox_inches='tight')
    plt.close(fig)
    
    return metrics, plot_path