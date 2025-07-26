# simulation/protocols/dsr.py
from .base_protocol import BaseProtocol
import logging

class DSR(BaseProtocol):
    """
    Implements the Dynamic Source Routing (DSR) protocol.
    It's a reactive protocol that uses source routing.
    """
    def __init__(self, env, node_id, network_env):
        super().__init__(env, node_id, network_env)
        self.route_cache = {}  # {destination: [path1, path2]}
        self.rreq_cache = {}  # { (source, rreq_id): timestamp }
        self.rreq_id_counter = 0
        self.pending_packets = {} # { destination: [packet] }
        
    def send_packet(self, destination_id, data="Default Data"):
        """Overrides base send to use source routing."""
        # Check cache for a route
        if destination_id in self.route_cache and self.route_cache[destination_id]:
            # Use the shortest cached route
            path = min(self.route_cache[destination_id], key=len)
            
            packet = {
                'type': 'data',
                'source': self.node_id,
                'destination': destination_id,
                'source_route': path,
                'path_index': 1, # Next node in the path to visit
                'data': data
            }
            logging.info(f"Time {self.env.now:.2f}: {self.node_id} (DSR) sending data to {destination_id} via {path}")
            self.env.process(self.forward_packet(packet))
        else:
            # No route found, initiate route discovery
            logging.info(f"Time {self.env.now:.2f}: {self.node_id} (DSR) no route to {destination_id}. Initiating RREQ.")
            self.initiate_route_discovery(destination_id, data)

    def initiate_route_discovery(self, destination_id, data):
        """Broadcasts an RREQ to find a route."""
        # Queue the packet
        if destination_id not in self.pending_packets:
            self.pending_packets[destination_id] = []
        # We need to store data with the packet for when the route is found
        self.pending_packets[destination_id].append(data)
        
        self.rreq_id_counter += 1
        rreq_packet = {
            'type': 'rreq',
            'rreq_id': self.rreq_id_counter,
            'source': self.node_id,
            'destination': destination_id,
            'path_taken': [self.node_id]
        }
        self.rreq_cache[(self.node_id, self.rreq_id_counter)] = self.env.now
        self.env.process(self.broadcast(rreq_packet))
        
    def receive_packet(self, packet):
        ptype = packet.get('type')
        if ptype == 'rreq':
            self.handle_rreq(packet)
        elif ptype == 'rrep':
            self.handle_rrep(packet)
        elif ptype == 'data':
            # Data packets in DSR have special forwarding logic
            self.env.process(self.forward_packet(packet))
        else:
            super().receive_packet(packet) # Fallback

    def handle_rreq(self, rreq):
        """Processes an RREQ, appending its ID to the path."""
        # Check for duplicates
        if (rreq['source'], rreq['rreq_id']) in self.rreq_cache:
            return
        
        self.rreq_cache[(rreq['source'], rreq['rreq_id'])] = self.env.now
        
        # Add self to the path
        current_path = rreq['path_taken'] + [self.node_id]
        self.cache_route(current_path[::-1]) # Cache reverse path
        
        if rreq['destination'] == self.node_id:
            # We are the destination, send RREP
            logging.info(f"Time {self.env.now:.2f}: {self.node_id} (DSR) is DEST for RREQ. Sending RREP.")
            self.send_rrep(rreq['source'], current_path)
        else:
            # Rebroadcast RREQ with updated path
            rreq['path_taken'] = current_path
            self.env.process(self.broadcast(rreq))

    def send_rrep(self, destination, path):
        """Sends an RREP back along the discovered path."""
        rrep_packet = {
            'type': 'rrep',
            'source': self.node_id,
            'destination': destination,
            'source_route': path[::-1] # Reverse the path for the reply
        }
        self.cache_route(rrep_packet['source_route'])
        # The RREP itself is source-routed
        self.env.process(self.forward_packet(rrep_packet))

    def handle_rrep(self, rrep):
        """Processes an RREP, caching the route and sending pending data."""
        self.cache_route(rrep['source_route'])
        
        # If we are the destination of the RREP (the original RREQ source)
        if rrep['destination'] == self.node_id:
            dest = rrep['source_route'][-1]
            if dest in self.pending_packets:
                logging.info(f"Time {self.env.now:.2f}: {self.node_id} (DSR) got RREP. Sending pending data.")
                for data in self.pending_packets.pop(dest):
                    self.send_packet(dest, data)
        else:
            # Forward the RREP
            self.env.process(self.forward_packet(rrep))

    def forward_packet(self, packet):
        """Specialized forwarding for source-routed packets."""
        route = packet['source_route']
        index = route.index(self.node_id)
        
        if index == len(route) - 1:
            # We are the final destination
            logging.info(f"Time {self.env.now:.2f}: {self.node_id} received final packet from {packet['source']}.")
            self.stats['packets_received'] += 1
            return
            
        next_hop_id = route[index + 1]
        neighbor = self.network_env.get_node(next_hop_id)
        if neighbor:
            yield self.env.timeout(0.05)
            neighbor.receive_packet(packet)
            self.stats['packets_sent'] += 1
            if packet.get('type') == 'data': # Only count data packets as relayed
                self.stats['packets_relayed'] += 1
        else:
            # Link is broken
            logging.warning(f"Time {self.env.now:.2f}: {self.node_id} could not find next hop {next_hop_id} in route.")
            self.stats['packets_dropped'] += 1
            # In a full implementation, send a Route Error (RERR) here.

    def cache_route(self, path):
        """Adds a discovered path to the route cache."""
        if not path: return
        dest = path[-1]
        if dest not in self.route_cache:
            self.route_cache[dest] = []
        if path not in self.route_cache[dest]:
            self.route_cache[dest].append(path)
            logging.info(f"Time {self.env.now:.2f}: {self.node_id} cached route to {dest}: {path}")