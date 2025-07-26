# simulation/protocols/aodv.py
from .base_protocol import BaseProtocol
import logging

class AODV(BaseProtocol):
    """
    Implements the Ad-hoc On-Demand Distance Vector (AODV) routing protocol.
    It's a reactive protocol that discovers routes only when needed.
    """
    def __init__(self, env, node_id, network_env):
        super().__init__(env, node_id, network_env)
        self.sequence_number = 0
        self.rreq_id = 0
        self.rreq_cache = {}  # { (initiator, rreq_id): timestamp }
        self.pending_packets = {} # { destination_id: [packet1, packet2] }
        # AODV routing table: {destination: (next_hop, hop_count, dest_seq_num, timestamp)}

    def forward_packet(self, packet):
        """Overrides base method to handle on-demand route discovery."""
        destination = packet['destination']
        
        # Check for a valid route in the table
        if destination in self.routing_table:
            logging.info(f"Time {self.env.now:.2f}: {self.node_id} (AODV) has route to {destination}. Forwarding.")
            # Use the BaseProtocol's forwarding logic, but we need to adapt it
            # since the base forward_packet does broadcasting if no route exists.
            next_hop_id = self.routing_table[destination][0]
            neighbor_node = self.network_env.get_node(next_hop_id)
            if neighbor_node:
                self.env.process(self.transmit_to_neighbor(neighbor_node, packet))
        else:
            # No route exists, initiate route discovery
            logging.info(f"Time {self.env.now:.2f}: {self.node_id} (AODV) NO route to {destination}. Initiating RREQ.")
            self.initiate_route_discovery(packet)
            
    def transmit_to_neighbor(self, neighbor_node, packet):
        """Helper coroutine for sending to a specific neighbor."""
        yield self.env.timeout(0.05) # Transmission delay
        neighbor_node.receive_packet(packet)
        self.stats['packets_sent'] += 1
        if packet['source'] != self.node_id:
            self.stats['packets_relayed'] += 1

    def initiate_route_discovery(self, packet):
        """Starts the RREQ process for a destination."""
        dest_id = packet['destination']
        
        # Queue the packet
        if dest_id not in self.pending_packets:
            self.pending_packets[dest_id] = []
        self.pending_packets[dest_id].append(packet)
        
        self.rreq_id += 1
        self.sequence_number += 1
        
        rreq_packet = {
            'type': 'rreq',
            'rreq_id': self.rreq_id,
            'source': self.node_id,
            'destination': dest_id,
            'source_seq': self.sequence_number,
            'hop_count': 0,
            'path': [self.node_id]
        }
        self.rreq_cache[(self.node_id, self.rreq_id)] = self.env.now
        self.env.process(self.broadcast(rreq_packet))
        
    def receive_packet(self, packet):
        ptype = packet.get('type')
        if ptype == 'rreq':
            self.handle_rreq(packet)
        elif ptype == 'rrep':
            self.handle_rrep(packet)
        else:
            super().receive_packet(packet)

    def handle_rreq(self, rreq):
        """Processes a received Route Request packet."""
        # Check if we've seen this RREQ before
        if (rreq['source'], rreq['rreq_id']) in self.rreq_cache:
            return # Duplicate RREQ, discard
        
        self.rreq_cache[(rreq['source'], rreq['rreq_id'])] = self.env.now
        
        # Set up reverse route
        self.routing_table[rreq['source']] = (rreq['path'][-1], rreq['hop_count'] + 1, rreq['source_seq'], self.env.now)

        if rreq['destination'] == self.node_id:
            # We are the destination, send an RREP
            logging.info(f"Time {self.env.now:.2f}: {self.node_id} (AODV) is DEST for RREQ. Sending RREP.")
            self.send_rrep(rreq)
        else:
            # We are an intermediate node, rebroadcast RREQ
            rreq['hop_count'] += 1
            rreq['path'].append(self.node_id)
            self.env.process(self.broadcast(rreq))

    def send_rrep(self, rreq):
        """Creates and sends a Route Reply packet."""
        self.sequence_number += 1
        rrep_packet = {
            'type': 'rrep',
            'source': self.node_id, # We are the source of the RREP
            'destination': rreq['source'], # The original source of the RREQ
            'dest_seq_num': self.sequence_number,
            'hop_count': 0,
            'path': [self.node_id]
        }
        
        # Unicast RREP back along the reverse path
        next_hop = self.routing_table[rreq['source']][0]
        neighbor = self.network_env.get_node(next_hop)
        if neighbor:
            self.env.process(self.transmit_to_neighbor(neighbor, rrep_packet))

    def handle_rrep(self, rrep):
        """Processes a received Route Reply packet."""
        # Set up forward route to the destination
        self.routing_table[rrep['source']] = (rrep['path'][-1], rrep['hop_count'] + 1, rrep['dest_seq_num'], self.env.now)
        
        if rrep['destination'] == self.node_id:
            # We are the original source, send pending packets
            logging.info(f"Time {self.env.now:.2f}: {self.node_id} (AODV) received RREP. Sending pending packets.")
            if rrep['source'] in self.pending_packets:
                for pkt in self.pending_packets.pop(rrep['source']):
                    self.env.process(self.forward_packet(pkt))
        else:
            # We are an intermediate node, forward the RREP
            rrep['hop_count'] += 1
            rrep['path'].append(self.node_id)
            next_hop = self.routing_table[rrep['destination']][0]
            neighbor = self.network_env.get_node(next_hop)
            if neighbor:
                self.env.process(self.transmit_to_neighbor(neighbor, rrep))