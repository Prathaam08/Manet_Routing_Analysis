# simulation/network_env.py
import random
import networkx as nx
import math

class NetworkEnvironment:
    """Manages the network state, node positions, and connectivity."""
    def __init__(self, env, area):
        self.env = env
        self.area = area  # Expected to be a tuple (width, height)
        self.nodes = {}   # To store node objects: {node_id: node_object}
        self.graph = nx.Graph()
        self.positions = {} # {node_id: (x, y)}

    def add_node(self, node_object):
        """Adds a new node to the environment with a random position."""
        node_id = node_object.node_id
        self.nodes[node_id] = node_object
        self.graph.add_node(node_id)
        
        # Assign a random position within the defined area
        x = random.uniform(0, self.area[0])
        y = random.uniform(0, self.area[1])
        self.positions[node_id] = (x, y)
        
    def get_node(self, node_id):
        """Retrieves a node object by its ID."""
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id, transmission_range):
        """Finds all nodes within the transmission range of a given node."""
        neighbors = []
        if node_id not in self.positions:
            return []
            
        p1 = self.positions[node_id]
        
        for other_id, p2 in self.positions.items():
            if node_id == other_id:
                continue
            
            # Calculate Euclidean distance
            distance = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
            
            if distance <= transmission_range:
                neighbors.append(self.nodes[other_id])
                
        return neighbors

    def get_full_positions_dict(self):
        """Returns the complete dictionary of node positions for plotting."""
        return self.positions