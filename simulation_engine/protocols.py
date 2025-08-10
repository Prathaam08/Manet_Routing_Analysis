# simulation_engine/protocols.py
import simpy
from collections import defaultdict, deque
from . import config  # read config.stop_simulation at runtime

class BaseRouting:
    def __init__(self, env, nodes, graph):
        self.env = env
        self.nodes = nodes
        # direct mapping for id -> Node
        self.node_map = {node.id: node for node in nodes}
        self.graph = graph
        self.routing_overhead = 0
        self.packet_queue = defaultdict(deque)
        # route_tables[node_id][dest_id] -> next_hop_id (or None)
        self.route_tables = {node.id: {} for node in nodes}

    def update_neighbors(self):
        """Update neighbor lists on node objects (store Node objects)."""
        for node in self.nodes:
            node.neighbors.clear()
            for other in self.nodes:
                if node.id != other.id and node.distance_to(other) <= node.tx_range:
                    node.neighbors.append(other)  # store Node object

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
                # node.receive is a generator, so schedule it
                self.env.process(node.receive(packet))
                yield self.env.timeout(0)
                continue

            # Known route? Forward packet
            if packet.dst_id in node.routing_table:
                next_hop_id = node.routing_table[packet.dst_id]
                # Only forward if next_hop is currently a neighbor (freshness check)
                if next_hop_id in [n.id for n in node.neighbors]:
                    packet.hops.append((node.id, self.env.now))
                    packet.last_hop = node.id

                    # Simulate transmission delay (e.g., 2 Mbps)
                    yield self.env.timeout(packet.size / (2 * 1024))

                    # Consume energy on transmission
                    node.consume_energy(0.1)

                    # Forward to next hop node object
                    next_hop_node = self.node_map.get(next_hop_id)
                    if next_hop_node:
                        self.env.process(next_hop_node.receive(packet))
                    else:
                        # next_hop_id invalid; drop or queue for rediscovery
                        # For now, we drop (could add pending packets)
                        pass
                    continue

            # No known route — let subclass handle routing discovery or fallback
            yield self.env.timeout(0.001)

    def get_overhead(self):
        return self.routing_overhead

    def get_next_hop(self, current_id, destination_id):
        """
        Return Node object for next hop from the route_tables, or None.
        route_tables stores next_hop_id (or dicts for DSDV legacy), so handle both.
        """
        table = self.route_tables.get(current_id, {})
        if table is None:
            return None

        entry = table.get(destination_id)
        # If entry is a dict (older DSDV style), extract next_hop
        if isinstance(entry, dict):
            next_hop_id = entry.get('next_hop')
        else:
            next_hop_id = entry

        if next_hop_id is None:
            return None

        return self.node_map.get(next_hop_id)


# ------------------ AODV ------------------
class AODV(BaseRouting):
    def __init__(self, env, nodes, graph):
        super().__init__(env, nodes, graph)
        self.rreq_id = 0
        self.pending_packets = defaultdict(list)  # key: (src_id, dst_id) -> list of Packet
        self.seq_num = 0
        # start periodic neighbor refresh
        self.env.process(self._periodic_neighbor_update())

    def _periodic_neighbor_update(self):
        while not config.stop_simulation:
            self.update_neighbors()
            yield self.env.timeout(1.0)

    def _route_packet(self, node, packet):
        """Return True if route exists and update node.routing_table with next_hop_id."""
        next_hop = self.route_tables.get(node.id, {}).get(packet.dst_id)
        # handle dict entry possibility
        if isinstance(next_hop, dict):
            next_hop = next_hop.get('next_hop')
        if next_hop is not None:
            node.routing_table[packet.dst_id] = next_hop
            return True
        return False

    def _route_discovery(self, src_node, packet):
        """Flood simplified RREQ for unknown destination."""
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

        # flood to neighbors (pass neighbor IDs into _forward_rreq)
        for neighbor in src_node.neighbors:
            self.env.process(self._forward_rreq(dict(rreq), neighbor.id))

    def _forward_rreq(self, rreq, node_id):
        """Process an RREQ at node with id node_id (node_id -> Node object at top)."""
        yield self.env.timeout(0.01)
        rreq['hop_count'] += 1
        rreq['ttl'] -= 1

        node = self.node_map.get(node_id)
        if not node:
            return

        # record reverse route: node -> src via last_hop (last_hop is an ID)
        if node.id != rreq['src_id']:
            # store next hop towards source as last_hop (which is an id)
            self.route_tables.setdefault(node.id, {})
            self.route_tables[node.id][rreq['src_id']] = rreq.get('last_hop')

        # If this node is the destination, generate a RREP back to src
        if node.id == rreq['dst_id']:
            # schedule sending RREP
            self.env.process(self._send_rrep(rreq, node.id))
            return

        # Otherwise flood further
        if rreq['ttl'] > 0:
            for neighbor in node.neighbors:
                if neighbor.id != rreq.get('last_hop'):
                    new_rreq = dict(rreq)
                    new_rreq['last_hop'] = node.id
                    self.env.process(self._forward_rreq(new_rreq, neighbor.id))

    def _send_rrep(self, rreq, dst_node_id):
        """
        Sends a Route Reply from dst_node back to src using reverse path stored in route_tables.
        This implementation traces backwards using stored next_hop ids.
        """
        yield self.env.timeout(0.01)
        path = []
        current = dst_node_id
        src = rreq['src_id']
        visited = set()

        # reconstruct reverse path from dst -> src using route_tables (next_hop entries point towards src)
        while True:
            path.append(current)
            if current == src:
                break
            visited.add(current)
            next_hop = self.route_tables.get(current, {}).get(src)
            # If we stored dictionaries in some cases, handle it
            if isinstance(next_hop, dict):
                next_hop = next_hop.get('next_hop')
            if next_hop is None or next_hop in visited:
                break
            current = next_hop

        # path is [dst,...,src] so reverse to [src,...,dst]
        path.reverse()

        # install forward routes along path (each node -> dst via next element)
        for i in range(len(path) - 1):
            node_id = path[i]
            next_hop_id = path[i + 1]
            self.route_tables.setdefault(node_id, {})
            self.route_tables[node_id][rreq['dst_id']] = next_hop_id
            # also update node's routing_table (node_map exists)
            node_obj = self.node_map.get(node_id)
            if node_obj:
                node_obj.routing_table[rreq['dst_id']] = next_hop_id

        self.routing_overhead += max(0, len(path) - 1)

        # flush pending packets
        pending = self.pending_packets.pop((rreq['src_id'], rreq['dst_id']), [])
        for pkt in pending:
            self.send_packet(pkt)

    def try_send(self, src_node, packet):
        """Try to route packet immediately; otherwise start discovery."""
        if self._route_packet(src_node, packet):
            self.send_packet(packet)
            return True
        self._route_discovery(src_node, packet)
        return False


# ------------------ DSDV ------------------
class DSDV(BaseRouting):
    def __init__(self, env, nodes, graph):
        super().__init__(env, nodes, graph)
        # We'll track both next_hop and metric in route_tables[node][dest] = {'next_hop':id, 'metric':num}
        for node in nodes:
            for other in nodes:
                if node.id == other.id:
                    self.route_tables[node.id][other.id] = {'next_hop': other.id, 'metric': 0}
                else:
                    self.route_tables[node.id][other.id] = {'next_hop': None, 'metric': float('inf')}
        self.env.process(self._periodic_update())
        self.env.process(self._periodic_neighbor_update())

    def _periodic_neighbor_update(self):
        while not config.stop_simulation:
            self.update_neighbors()
            yield self.env.timeout(2.0)

    def _periodic_update(self):
        """Periodically exchange routing information with neighbors (distance-vector style)."""
        while not config.stop_simulation:
            for node in self.nodes:
                for neighbor in node.neighbors:
                    # each neighbor learns this node's table entries
                    self.routing_overhead += len(self.route_tables[node.id])
                    for dest, route in list(self.route_tables[node.id].items()):
                        # compute metric via node -> neighbor
                        new_metric = route['metric'] + 1
                        neighbor_table = self.route_tables[neighbor.id]
                        # if neighbor has no entry for dest or new metric better -> update
                        if new_metric < neighbor_table[dest]['metric']:
                            neighbor_table[dest] = {'next_hop': node.id, 'metric': new_metric}
                            # also reflect in node_map's routing_table (next_hop id)
                            neighbor_obj = self.node_map.get(neighbor.id)
                            if neighbor_obj:
                                neighbor_obj.routing_table[dest] = node.id
            yield self.env.timeout(5.0)

    def _route_packet(self, node, packet):
        """If DSDV table has a next_hop, place it in node.routing_table."""
        entry = self.route_tables.get(node.id, {}).get(packet.dst_id)
        if entry and entry.get('next_hop') is not None:
            node.routing_table[packet.dst_id] = entry.get('next_hop')
            return True
        return False


# ------------------ DSR ------------------
class DSR(BaseRouting):
    def __init__(self, env, nodes, graph):
        super().__init__(env, nodes, graph)
        self.route_cache = {}  # key: (src, dst) -> [path of node ids]
        self.env.process(self._periodic_neighbor_update())

    def _periodic_neighbor_update(self):
        while not config.stop_simulation:
            self.update_neighbors()
            yield self.env.timeout(1.0)

    def _route_packet(self, node, packet):
        """
        If route cache has a full source route, install the next hop for the sender node.
        route_cache stores full lists of node ids [src, ..., dst].
        """
        key = (packet.src_id, packet.dst_id)
        if key in self.route_cache:
            route = self.route_cache[key]
            if node.id in route:
                idx = route.index(node.id) + 1
                if idx < len(route):
                    next_hop_id = route[idx]
                    node.routing_table[packet.dst_id] = next_hop_id
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
        """Simplified MPR selection where every neighbor is considered an MPR."""
        while not config.stop_simulation:
            for node in self.nodes:
                # store MPR ids
                node.mprs = [n.id for n in node.neighbors]
                for mpr in node.mprs:
                    self.mpr_selectors.setdefault(mpr, set()).add(node.id)
            yield self.env.timeout(10.0)

    def _route_packet(self, node, packet):
        """
        For OLSR, check if destination reachable in route table.
        If yes, update node.routing_table with next_hop_id.
        """
        entry = self.route_tables.get(node.id, {}).get(packet.dst_id)
        # entry could be dict or next_hop id
        if isinstance(entry, dict):
            next_hop_id = entry.get('next_hop')
        else:
            next_hop_id = entry
        if next_hop_id is not None:
            node.routing_table[packet.dst_id] = next_hop_id
            return True
        return False
