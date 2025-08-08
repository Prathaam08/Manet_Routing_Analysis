import simpy
import random
import heapq
from collections import defaultdict, deque
from .config import stop_simulation,reset  # Import the shared stop flag

class BaseRouting:
    def __init__(self, env, nodes, graph):
        self.env = env
        self.nodes = nodes
        self.graph = graph
        self.routing_overhead = 0
        self.packet_queue = defaultdict(deque)
        self.route_tables = {node.id: {} for node in nodes}
        
    def update_neighbors(self):
        for node in self.nodes:
            node.neighbors = []
            for other in self.nodes:
                if node.id != other.id and node.distance_to(other) <= node.tx_range:
                    node.neighbors.append(other)
    
    def send_packet(self, packet):
        src_node = self.nodes[packet.src_id]
        self.packet_queue[src_node.id].append(packet)
        if not hasattr(src_node, 'packet_handler') or src_node.packet_handler.processed:
            src_node.packet_handler = self.env.process(self._handle_packets(src_node))
    
    def _handle_packets(self, node):
        while self.packet_queue[node.id]:
            packet = self.packet_queue[node.id].popleft()
            if packet.dst_id == node.id:
                # Packet reached destination
                packet.delivery_time = self.env.now
                node.simulator.metrics['packets_received'] += 1
                node.simulator.interval_metrics['packets_received'] += 1
                delay = packet.delivery_time - packet.creation_time
                node.simulator.metrics['total_delay'] += delay
                node.simulator.interval_metrics['total_delay'] += delay
            else:
                # Forward packet
                if packet.dst_id in node.routing_table:
                    next_hop = node.routing_table[packet.dst_id]
                    if next_hop in [n.id for n in node.neighbors]:
                        # Record hop
                        packet.hops.append((node.id, self.env.now))
                        packet.last_hop = node.id
                        
                        # Simulate transmission delay
                        transmission_time = packet.size / (2 * 1024)  # 2 Mbps link
                        yield self.env.timeout(transmission_time)
                        
                        # Energy consumption
                        node.consume_energy(0.1)  # 0.1J per packet
                        
                        # Send to next hop
                        self.env.process(self.nodes[next_hop].receive(packet))
    
    def get_overhead(self):
        return self.routing_overhead

class AODV(BaseRouting):
    def __init__(self, env, nodes, graph):
        super().__init__(env, nodes, graph)
        self.rreq_id = 0
        self.route_requests = {}
        self.seq_num = 0
        self.env.process(self._periodic_neighbor_update())
    
    def _periodic_neighbor_update(self):
        while True:
            if stop_simulation:  # Add stop condition
                return
            self.update_neighbors()
            yield self.env.timeout(1.0)
    
    def _route_packet(self, node, packet):
        # If no route exists, start route discovery
        if packet.dst_id not in self.route_tables[node.id]:
            self.env.process(self._route_discovery(node, packet))
            return False
        return super()._route_packet(node, packet)
    
    def _route_discovery(self, src_node, packet):
        # Broadcast RREQ
        self.rreq_id += 1
        rreq = {
            'src_id': src_node.id,
            'dst_id': packet.dst_id,
            'rreq_id': self.rreq_id,
            'src_seq': self.seq_num,
            'dst_seq': 0,
            'hop_count': 0,
            'ttl': 10
        }
        self.seq_num += 1
        self.route_requests[(src_node.id, self.rreq_id)] = rreq
        self.routing_overhead += 1
        
        # Broadcast to neighbors
        for neighbor in src_node.neighbors:
            if neighbor.id != src_node.id:
                self.env.process(self._forward_rreq(rreq, neighbor.id))
    
    def _forward_rreq(self, rreq, node_id):
        node = self.nodes[node_id]
        rreq['hop_count'] += 1
        rreq['ttl'] -= 1
        
        # Record reverse path
        if node_id != rreq['src_id']:
            self.route_tables[node_id][rreq['src_id']] = rreq['last_hop']
        
        # If destination reached, send RREP
        if node_id == rreq['dst_id']:
            self.env.process(self._send_rrep(rreq, node))
            return
        
        # Re-broadcast if TTL remains
        if rreq['ttl'] > 0:
            for neighbor in node.neighbors:
                if neighbor.id != rreq['last_hop']:
                    new_rreq = rreq.copy()
                    new_rreq['last_hop'] = node_id
                    self.env.process(self._forward_rreq(new_rreq, neighbor.id))
    
    def _send_rrep(self, rreq, dst_node):
        # Build reverse path back to source
        path = []
        current = dst_node.id
        while current != rreq['src_id']:
            path.append(current)
            current = self.route_tables[current][rreq['src_id']]
        path.append(rreq['src_id'])
        path.reverse()
        
        # Update routing tables along the path
        for i in range(len(path)-1):
            self.route_tables[path[i]][rreq['dst_id']] = path[i+1]
        
        # Send RREP back along the path
        for i in range(len(path)-1, 0, -1):
            node = self.nodes[path[i]]
            neighbor = self.nodes[path[i-1]]
            # Simulate transmission
            yield self.env.timeout(0.01)
            self.routing_overhead += 1

class DSDV(BaseRouting):
    def __init__(self, env, nodes, graph):
        super().__init__(env, nodes, graph)
        # Initialize routing tables
        self.route_tables = {node.id: {} for node in nodes}
        for node in nodes:
            for other in nodes:
                if node.id == other.id:
                    self.route_tables[node.id][other.id] = {'next_hop': other.id, 'metric': 0}
                else:
                    self.route_tables[node.id][other.id] = {'next_hop': None, 'metric': float('inf')}
        
        # Periodically update routes
        self.env.process(self._periodic_update())
        self.env.process(self._periodic_neighbor_update())
    
    def _periodic_neighbor_update(self):
        while True:
            if stop_simulation:
                return
            self.update_neighbors()
            yield self.env.timeout(2.0)

    
    def _periodic_update(self):
        while True:
            # Each node broadcasts its routing table
            for node in self.nodes:
                for neighbor in node.neighbors:
                    # Send full routing table to neighbor
                    self.routing_overhead += len(self.route_tables[node.id])
                    # Update neighbor's routing table
                    for dest, route in self.route_tables[node.id].items():
                        new_metric = route['metric'] + 1
                        if new_metric < self.route_tables[neighbor.id][dest]['metric']:
                            self.route_tables[neighbor.id][dest] = {
                                'next_hop': node.id,
                                'metric': new_metric
                            }
            yield self.env.timeout(5.0)  # Update every 5 seconds
    
    def _route_packet(self, node, packet):
        route = self.route_tables[node.id].get(packet.dst_id)
        if route and route['next_hop']:
            node.routing_table[packet.dst_id] = route['next_hop']
            return super()._route_packet(node, packet)
        return False

# Simplified implementations for DSR and OLSR
class DSR(BaseRouting):
    def __init__(self, env, nodes, graph):
        super().__init__(env, nodes, graph)
        self.route_cache = {}
        self.env.process(self._periodic_neighbor_update())

    def _periodic_neighbor_update(self):
        while True:
            self.update_neighbors()
            yield self.env.timeout(1.0)
    
    def _route_packet(self, node, packet):
        if (packet.src_id, packet.dst_id) in self.route_cache:
            route = self.route_cache[(packet.src_id, packet.dst_id)]
            if node.id in route:
                next_index = route.index(node.id) + 1
                if next_index < len(route):
                    node.routing_table[packet.dst_id] = route[next_index]
                    return super()._route_packet(node, packet)
        return False

class OLSR(BaseRouting):
    def __init__(self, env, nodes, graph):
        super().__init__(env, nodes, graph)
        self.mpr_selectors = {}
        self.env.process(self._periodic_neighbor_update())
        self.env.process(self._mpr_selection())

    def _periodic_neighbor_update(self):
        while True:
            self.update_neighbors()
            yield self.env.timeout(1.0)
    
    def _mpr_selection(self):
        while True:
            for node in self.nodes:
                # Simplified MPR selection: choose all neighbors
                node.mprs = [n.id for n in node.neighbors]
                for mpr in node.mprs:
                    if mpr not in self.mpr_selectors:
                        self.mpr_selectors[mpr] = set()
                    self.mpr_selectors[mpr].add(node.id)
            yield self.env.timeout(10.0)
    
    def _route_packet(self, node, packet):
        # Use Dijkstra's algorithm for routing
        if packet.dst_id in self.route_tables.get(node.id, {}):
            return super()._route_packet(node, packet)
        return False