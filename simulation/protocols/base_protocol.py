# simulation/protocols/base_protocol.py
import simpy
from collections import deque
import logging

# Basic logging setup
logging.basicConfig(level=logging.INFO)

class BaseProtocol:
    """A fully functional base class for all routing protocols."""
    
    def __init__(self, env, node_id, network_env, transmission_range=150):
        self.env = env
        self.node_id = node_id
        self.network_env = network_env
        self.transmission_range = transmission_range

        # Data structures for the node
        self.routing_table = {}  # {destination_id: next_hop_id}
        self.packet_queue = deque()

        # Statistics for performance analysis
        self.stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'packets_relayed': 0,
            'packets_dropped': 0,
            'route_discoveries': 0
        }

        # Start the node's main processes
        self.env.process(self.run())
        self.env.process(self.receive_handler())

    def __repr__(self):
        return f"Node({self.node_id})"

    def run(self):
        """
        🧠 Main process for the node's lifecycle.
        This includes periodic tasks like neighbor discovery.
        """
        while True:
            # Periodically discover neighbors
            self.discover_neighbors()
            
            # Protocol-specific periodic tasks (e.g., DSDV updates) can be added here
            # by overriding this method in child classes.
            
            # Wait for a random interval before the next cycle
            yield self.env.timeout(1) # Discover neighbors every 1 second

    def discover_neighbors(self):
        """Finds and updates direct neighbors within transmission range."""
        # This method relies on the network_env to find nodes in range.
        # For simplicity in this base class, we don't store a persistent neighbor list,
        # but child protocols might.
        pass # The logic for finding who to send to is in `send_packet`.
        
    def receive_handler(self):
        """
        📥 Processes packets from the internal queue.
        This runs as a continuous background process for the node.
        """
        while True:
            if not self.packet_queue:
                yield self.env.timeout(0.01)  # Wait briefly if queue is empty
                continue

            packet = self.packet_queue.popleft()
            destination = packet['destination']

            if destination == self.node_id:
                # This packet is for me
                logging.info(f"Time {self.env.now:.2f}: {self.node_id} received final packet from {packet['source']}.")
                self.stats['packets_received'] += 1
            else:
                # I need to forward (relay) this packet
                self.forward_packet(packet)

    def send_packet(self, destination_id, data="Default Data"):
        """
        📡 Initiates the process of sending a packet to a final destination.
        """
        packet = {
            'type': 'data',
            'source': self.node_id,
            'destination': destination_id,
            'path': [self.node_id],
            'data': data
        }
        
        logging.info(f"Time {self.env.now:.2f}: {self.node_id} wants to send packet to {destination_id}.")
        
        # This method is a simplified entry point.
        # The actual forwarding logic is in `forward_packet`.
        self.forward_packet(packet)

    def forward_packet(self, packet):
        """Determines the next hop and transmits the packet."""
        destination = packet['destination']
        
        # Basic routing logic: If we have a route, use it.
        # In a real protocol, this would be more complex (e.g., AODV route discovery)
        if destination in self.routing_table:
            next_hop_id = self.routing_table[destination]
            logging.info(f"Time {self.env.now:.2f}: {self.node_id} forwarding packet for {destination} via {next_hop_id}.")
            
            # Find the actual neighbor node object to send to
            neighbor_node = self.network_env.get_node(next_hop_id)
            if neighbor_node:
                # Simulate transmission delay
                yield self.env.timeout(0.05) 
                neighbor_node.receive_packet(packet)
                self.stats['packets_sent'] += 1
                if packet['source'] != self.node_id:
                    self.stats['packets_relayed'] += 1
            else:
                logging.warning(f"Time {self.env.now:.2f}: {self.node_id} could not find next hop node {next_hop_id}.")
                self.stats['packets_dropped'] += 1
        else:
            # No route found, broadcast for now (simple default behavior)
            # AODV/DSR would start route discovery here.
            logging.info(f"Time {self.env.now:.2f}: {self.node_id} has no route to {destination}. Broadcasting.")
            self.broadcast(packet)
            
    def broadcast(self, packet):
        """Sends a packet to all neighbors within transmission range."""
        self.stats['packets_sent'] += 1 # Count broadcast as one send operation
        
        neighbors = self.network_env.get_neighbors(self.node_id, self.transmission_range)
        logging.info(f"Time {self.env.now:.2f}: {self.node_id} broadcasting to neighbors: {[n.node_id for n in neighbors]}.")
        
        for neighbor_node in neighbors:
            # Create a copy to avoid nodes modifying the same packet object
            packet_copy = packet.copy()
            # Avoid sending the packet back to the node that just sent it to us
            if neighbor_node.node_id not in packet_copy['path']:
                packet_copy['path'] = packet['path'] + [self.node_id]
                yield self.env.timeout(0.01) # Stagger broadcast transmissions slightly
                neighbor_node.receive_packet(packet_copy)

    def receive_packet(self, packet):
        """The entry point for an incoming packet from another node."""
        # Simply add the packet to the queue for processing by receive_handler
        self.packet_queue.append(packet)