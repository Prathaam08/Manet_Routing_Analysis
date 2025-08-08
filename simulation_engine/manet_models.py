import math
import numpy as np
import random
from .config import stop_simulation ,reset # Import the shared stop flag

class Node:
    def __init__(self, id, position, area_size, speed=10, pause_time=5, tx_range=100):
        self.id = id
        self.position = np.array(position, dtype=float)
        self.area_size = area_size
        self.speed = speed
        self.pause_time = pause_time
        self.tx_range = tx_range
        self.neighbors = []
        self.routing_table = {}
        self.energy = 100  # Initial energy in Joules
        self.energy_used = 0.0
        self.direction = np.array([random.uniform(-1, 1), random.uniform(-1, 1)])
        norm = np.linalg.norm(self.direction)
        if norm > 0:
            self.direction /= norm
        self.move_timer = 0
        
    def move(self, env):
        while True:
            if stop_simulation:  # Add stop condition
                return
            # Set new random direction and duration
            self.direction = np.array([random.uniform(-1, 1), random.uniform(-1, 1)])
            norm = np.linalg.norm(self.direction)
            if norm > 0:
                self.direction /= norm
            
            move_duration = self.pause_time
            
            # Move for the duration
            start_time = env.now
            while env.now - start_time < move_duration:
                # Update position
                self.position += self.direction * self.speed * 0.1  # Small time step
                
                # Boundary check with bounce
                for i in range(2):
                    if self.position[i] < 0:
                        self.position[i] = 0
                        self.direction[i] = abs(self.direction[i])
                    elif self.position[i] > self.area_size[i]:
                        self.position[i] = self.area_size[i]
                        self.direction[i] = -abs(self.direction[i])
                
                # Consume energy during movement
                self.consume_energy(0.01 * self.speed)
                yield env.timeout(0.1)
            
            # Pause at destination
            yield env.timeout(self.pause_time)
    
    def distance_to(self, other_node):
        return np.linalg.norm(self.position - other_node.position)
    
    def consume_energy(self, amount):
        self.energy -= amount
        self.energy_used += amount
        if self.energy < 0:
            self.energy = 0

class Packet:
    def __init__(self, src_id, dst_id, creation_time, size=512):
        self.src_id = src_id
        self.dst_id = dst_id
        self.creation_time = creation_time
        self.size = size
        self.hops = []
        self.last_hop = src_id
        self.delivery_time = None