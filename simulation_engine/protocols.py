import simpy
from collections import defaultdict, deque
from . import config  # read config.stop_simulation at runtime

class BaseRouting:
    def __init__(self, env, nodes, graph):
        self.env = env
        self.nodes = nodes
        self.node_map = {node.id: node for node in nodes}  # direct mapping for id -> Node
        self.graph = graph
        self.routing_overhead = 0
        self.packet_queue = defaultdict(deque)
        self.route_tables = {node.id: {} for node in nodes}  # dest_id -> next_hop_id mapping per node

    def update_neighbors(self):
        """Update neighbors list based on tx_range and position for each node."""
        for node in self.nodes:
            node.neighbors = [
                other for other in self.nodes
                if node.id != other.id and node.distance_to(other) <= node.tx_range
            ]

    def send_packet(self, packet):
        """Queue a Packet instance at the source node and start handling if not already running."""
        src_node = self.node_map[packet.src_id]
        self.packet_queue[src_node.id].append(packet)

        if not getattr(src_node, 'routing_handler_running', False):
            src_node.routing_handler_running = True

            def _handler_wrapper():
                yield from self._handle_packets(src_node)
                src_node.routing_handler_running = False

            self.env.process(_handler_wrapper())

    def _handle_packets(self, node):
        """SimPy generator to process queued packets for a node."""
        while self.packet_queue[node.id]:
            packet = self.packet_queue[node.id].popleft()

            # Packet reached destination
            if packet.dst_id == node.id:
                self.env.process(node.receive(packet))
                yield self.env.timeout(0)
                continue

            # Known route? Forward packet
            if packet.dst_id in node.routing_table:
                next_hop_id = node.routing_table[packet.dst_id]
                if next_hop_id in [n.id for n in node.neighbors]:
                    packet.hops.append((node.id, self.env.now))
                    packet.last_hop = node.id

                    # Simulate transmission delay (e.g., 2 Mbps)
                    yield self.env.timeout(packet.size / (2 * 1024))

                    # Consume energy on transmission
                    node.consume_energy(0.1)

                    # Forward to next hop node object
                    next_hop_node = self.node_map[next_hop_id]
                    self.env.process(next_hop_node.receive(packet))
                    continue

            # No known route — let subclass handle routing discovery or fallback
            yield self.env.timeout(0.001)

    def get_overhead(self):
        return self.routing_overhead

    def get_next_hop(self, current_id, destination_id):
        """Return next hop ID from route table or None."""
        return self.route_tables.get(current_id, {}).get(destination_id, None)


# ------------------ AODV ------------------
class AODV(BaseRouting):
    def __init__(self, env, nodes, graph):
        super().__init__(env, nodes, graph)
        self.rreq_id = 0
        self.pending_packets = defaultdict(list)
        self.seq_num = 0
        self.env.process(self._periodic_neighbor_update())

    def _periodic_neighbor_update(self):
        while not config.stop_simulation:
            self.update_neighbors()
            yield self.env.timeout(1.0)

    def _route_packet(self, node, packet):
        """Return True if route exists and update node routing_table."""
        if packet.dst_id in self.route_tables.get(node.id, {}):
            node.routing_table[packet.dst_id] = self.route_tables[node.id][packet.dst_id]
            return True
        return False

    def _route_discovery(self, src_node, packet):
        """Flood route requests (RREQ) for unknown destination."""
        self.rreq_id += 1
        rreq = {
            'src_id': src_node.id,
            'dst_id': packet.dst_id,
            'rreq_id': self.rreq_id,
            'src_seq': self.seq_num,
            'dst_seq': 0,
            'hop_count': 0,
            'ttl': 10,
            'last_hop': src_node.id
        }
        self.seq_num += 1

        self.pending_packets[(src_node.id, packet.dst_id)].append(packet)
        self.routing_overhead += 1

        for neighbor in src_node.neighbors:
            self.env.process(self._forward_rreq(dict(rreq), neighbor.id))

    def _forward_rreq(self, rreq, node_id):
        yield self.env.timeout(0.01)
        rreq['hop_count'] += 1
        rreq['ttl'] -= 1

        if node_id != rreq['src_id']:
            self.route_tables[node_id][rreq['src_id']] = rreq.get('last_hop')

        if node_id == rreq['dst_id']:
            self.env.process(self._send_rrep(rreq, node_id))
            return

        if rreq['ttl'] > 0:
            node = self.node_map[node_id]
            for neighbor in node.neighbors:
                if neighbor.id != rreq.get('last_hop'):
                    new_rreq = dict(rreq)
                    new_rreq['last_hop'] = node_id
                    self.env.process(self._forward_rreq(new_rreq, neighbor.id))

    def _send_rrep(self, rreq, dst_node_id):
        yield self.env.timeout(0.01)
        path = []
        current = dst_node_id
        src = rreq['src_id']
        visited = set()

        while True:
            path.append(current)
            if current == src:
                break
            visited.add(current)
            next_hop = self.route_tables.get(current, {}).get(src)
            if next_hop is None or next_hop in visited:
                break
            current = next_hop

        path.reverse()

        for i in range(len(path) - 1):
            node_id = path[i]
            next_hop = path[i + 1]
            self.route_tables[node_id][rreq['dst_id']] = next_hop
            self.node_map[node_id].routing_table[rreq['dst_id']] = next_hop

        self.routing_overhead += max(0, len(path) - 1)

        pending = self.pending_packets.pop((rreq['src_id'], rreq['dst_id']), [])
        for pkt in pending:
            self.send_packet(pkt)

    def try_send(self, src_node, packet):
        if self._route_packet(src_node, packet):
            self.send_packet(packet)
            return True
        self._route_discovery(src_node, packet)
        return False


# ------------------ DSDV ------------------
class DSDV(BaseRouting):
    def __init__(self, env, nodes, graph):
        super().__init__(env, nodes, graph)
        # Initialize route tables with metrics
        for node in nodes:
            for other in nodes:
                self.route_tables[node.id][other.id] = {
                    'next_hop': other.id if node.id == other.id else None,
                    'metric': 0 if node.id == other.id else float('inf')
                }
        self.env.process(self._periodic_update())
        self.env.process(self._periodic_neighbor_update())

    def _periodic_neighbor_update(self):
        while not config.stop_simulation:
            self.update_neighbors()
            yield self.env.timeout(2.0)

    def _periodic_update(self):
        while not config.stop_simulation:
            for node in self.nodes:
                for neighbor in node.neighbors:
                    self.routing_overhead += len(self.route_tables[node.id])
                    for dest, route in self.route_tables[node.id].items():
                        new_metric = route['metric'] + 1
                        if new_metric < self.route_tables[neighbor.id][dest]['metric']:
                            self.route_tables[neighbor.id][dest] = {
                                'next_hop': node.id,
                                'metric': new_metric
                            }
            yield self.env.timeout(5.0)

    def _route_packet(self, node, packet):
        route = self.route_tables.get(node.id, {}).get(packet.dst_id)
        if route and route['next_hop'] is not None:
            node.routing_table[packet.dst_id] = route['next_hop']
            return True
        return False


# ------------------ DSR ------------------
class DSR(BaseRouting):
    def __init__(self, env, nodes, graph):
        super().__init__(env, nodes, graph)
        self.route_cache = {}
        self.env.process(self._periodic_neighbor_update())

    def _periodic_neighbor_update(self):
        while not config.stop_simulation:
            self.update_neighbors()
            yield self.env.timeout(1.0)

    def _route_packet(self, node, packet):
        key = (packet.src_id, packet.dst_id)
        if key in self.route_cache:
            route = self.route_cache[key]
            if node.id in route:
                idx = route.index(node.id) + 1
                if idx < len(route):
                    node.routing_table[packet.dst_id] = route[idx]
                    return True
        return False


# ------------------ OLSR ------------------
class OLSR(BaseRouting):
    def __init__(self, env, nodes, graph):
        super().__init__(env, nodes, graph)
        self.mpr_selectors = {}
        self.env.process(self._periodic_neighbor_update())
        self.env.process(self._mpr_selection())

    def _periodic_neighbor_update(self):
        while not config.stop_simulation:
            self.update_neighbors()
            yield self.env.timeout(1.0)

    def _mpr_selection(self):
        while not config.stop_simulation:
            for node in self.nodes:
                # Simplified MPR selection: all neighbors as MPRs
                node.mprs = [n.id for n in node.neighbors]
                for mpr in node.mprs:
                    self.mpr_selectors.setdefault(mpr, set()).add(node.id)
            yield self.env.timeout(10.0)

    def _route_packet(self, node, packet):
        """
        For OLSR, check if destination reachable in route table.
        If yes, update routing_table and return True.
        """
        if packet.dst_id in self.route_tables.get(node.id, {}):
            node.routing_table[packet.dst_id] = self.route_tables[node.id][packet.dst_id]
            return True
        return False
