# simulation/protocols/dsdv.py
from .base_protocol import BaseProtocol
import logging

class DSDV(BaseProtocol):
    """
    Implements the Destination-Sequenced Distance-Vector (DSDV) routing protocol.
    It's a proactive protocol that maintains a routing table for all destinations.
    """
    def __init__(self, env, node_id, network_env, update_interval=5):
        super().__init__(env, node_id, network_env)
        self.update_interval = update_interval
        
        # DSDV routing table: {destination: (next_hop, metric, seq_num)}
        # The metric is the hop count.
        self.own_sequence_number = 0
        self.routing_table = {self.node_id: (self.node_id, 0, self.own_sequence_number)}
        
        # Override the base run process with DSDV's periodic updates
        self.env.process(self.run())

    def run(self):
        """Periodically broadcasts the node's routing table."""
        while True:
            # Increment own sequence number before broadcasting
            self.own_sequence_number += 2
            self.routing_table[self.node_id] = (self.node_id, 0, self.own_sequence_number)
            
            self.broadcast_routing_table()
            
            yield self.env.timeout(self.update_interval)

    def broadcast_routing_table(self):
        """Sends the entire routing table to all direct neighbors."""
        update_packet = {
            'type': 'routing_update',
            'source': self.node_id,
            'table': self.routing_table,
            'path': [self.node_id] # For broadcast mechanism
        }
        logging.info(f"Time {self.env.now:.2f}: {self.node_id} (DSDV) broadcasting its routing table.")
        self.env.process(self.broadcast(update_packet))

    def receive_packet(self, packet):
        """Handles incoming packets, specifically routing updates."""
        if packet.get('type') == 'routing_update':
            self.handle_routing_update(packet)
        else:
            # For data packets, use the base class handler
            super().receive_packet(packet)

    def handle_routing_update(self, packet):
        """Updates the routing table based on a received advertisement."""
        sender_id = packet['source']
        received_table = packet['table']
        
        for dest, (next_hop, metric, seq_num) in received_table.items():
            # Rule 1: If we have no info about the destination, add it.
            if dest not in self.routing_table:
                self.update_route(dest, sender_id, metric + 1, seq_num)
                continue

            current_next_hop, current_metric, current_seq_num = self.routing_table[dest]
            
            # Rule 2: Update if the new sequence number is higher.
            if seq_num > current_seq_num:
                self.update_route(dest, sender_id, metric + 1, seq_num)
            
            # Rule 3: If sequence numbers are equal, update if the new metric is better.
            elif seq_num == current_seq_num and (metric + 1) < current_metric:
                self.update_route(dest, sender_id, metric + 1, seq_num)

    def update_route(self, dest, next_hop, metric, seq_num):
        """Helper function to update a route and log the change."""
        logging.info(f"Time {self.env.now:.2f}: {self.node_id} updated route for {dest}: NextHop->{next_hop}, Metric->{metric}, Seq->{seq_num}")
        self.routing_table[dest] = (next_hop, metric, seq_num)