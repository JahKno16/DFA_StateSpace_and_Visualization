import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from Visualizer import ModularVisualizer
from read_matrix import read_matrix_from_serial
import time

from itertools import combinations, product, permutations

class DynamicDFA:
    def __init__(self, num_modules):
        self.num_modules = num_modules
        self.states = set()  # Set of all states
        self.transitions = {}  # Dictionary of transitions between states
        self.graph = nx.DiGraph()  # Directed graph to visualize the DFA
        self.current_state = None  # Start state
        self.define_connections()
        self.generate_states()
        self.occupied = {}
       
    def define_connections(self):
        self.femalePorts = ["P1", "P2", "P3"]
        self.malePorts = ["P4", "P5", "P6"]
        self.orientations = ["O1", "O2"]
       
    def generate_states(self):
        start_state = frozenset({'M0_0'})
        self.states.add(start_state)
        self.current_state = start_state

        for num_connected in range(1, self.num_modules + 1):
            for modules in permutations(range(self.num_modules), num_connected):
               
               
                state_items = [[] for _ in range(len(modules) - 1)]
                for i, module in enumerate(modules):
                    if i < len(modules) - 1:
                        for connections in product(self.malePorts, self.femalePorts, self.orientations):
                            mPort, fPort, orientation = connections
                            # Connect this module with the next module in the list
                            next_module = modules[i + 1]
                            state_item = (f'M{module + 1}_{fPort}', f'M{next_module + 1}_{mPort}_{orientation}')
                            state_items[i].append(state_item) 
                    for state_combination in product(*state_items):
                        state = frozenset(state_combination)
                        self.add_state(state)
        #print(self.states)

        # Generate transitions for each state
        for state in list(self.states):
            self.generate_transitions_for_state(state)

    def add_state(self, state, is_start=False):
        self.states.add(state)
        self.graph.add_node(state)
        if is_start:
            self.current_state = state

    def generate_transitions_for_state(self, state):
        possible_actions = self.generate_possible_actions()
        for action in possible_actions:
            new_state = self.apply_action(state, action)
            if new_state in self.states:
                self.add_transition(state, action, new_state)


    def add_transition(self, from_state, action, to_state, reset=False):
        if from_state not in self.states or to_state not in self.states:
            raise ValueError(f"Both from_state '{from_state}' and to_state '{to_state}' must be valid states.")
        
        if reset:
            to_state = from_state  # Set the transition to loop back to the from_state
        
        self.transitions[(from_state, action)] = to_state
        self.graph.add_edge(from_state, to_state, label=action)

    #Generates all possible actions between states
    def generate_possible_actions(self):
        actions = []
        for i in range(self.num_modules):
            for j in range(self.num_modules):
                if i != j:
                    for connections in product(self.malePorts, self.femalePorts, self.orientations):
                        mPort, fPort, orientation = connections
                        actions.append(f'connect_M{i+1}_{fPort}_M{j+1}_{mPort}_{orientation}')
            for fPort in self.femalePorts:
                actions.append(f'disconnect_M{i+1}_{fPort}')
        #print(actions)
        return actions

    #Applies possible actions to produce a new states
    def apply_action(self, state, action):
        state_dict = dict(state)
        parts = action.split('_')
    
        if 'disconnect' in action:
            # Module-to-module disconnect
            module, fPort = parts[1], parts[2]
            state_dict.pop(f'{module}_{fPort}', None)

        elif 'connect' in action:
            module, nextModule = parts[1], parts[3] # Extract module nnumbers
            fPort, mPort, orient = parts[2], parts[4], parts[5] # Connection points
            state_dict[f'{module}_{fPort}'] = f'{nextModule}_{mPort}_{orient}'

        return frozenset(state_dict.items())


    def perform_action(self, action):
        if self.current_state is None:
            raise ValueError("Start state is not set.")
        
        if (self.current_state, action) in self.transitions:
            new_state = self.transitions[(self.current_state, action)]
            print(f"Transitioning from {self.current_state} to {new_state} on action '{action}'")
            self.current_state = new_state
        
            visualizer = ModularVisualizer()
            visualizer.visualize_configuration(self.current_state)
        else:
            print(f"No valid transition from state '{self.current_state}' on action '{action}'")

    def action_config_matrix(self, matrix):
        actions = []
        for module_idx, row in enumerate(matrix):
            for port_idx, val in enumerate(row):
                occupied_key = (module_idx, port_idx)
                if val != 0:
                    if occupied_key not in self.occupied:
                        self.occupied[occupied_key] = True

                        binary_val = format(val, '08b')
                        port_num = int(binary_val[-3:], 2)
                        module_num = int(binary_val[:5], 2)

                        actions.append(f'connect_M{module_idx+1}_P{port_idx+1}_M{module_num}_P{port_num}_O1')
                        print(f'M{module_idx+1}_P{port_idx+1}_M{module_num}_P{port_num}')
                else: 
                    if occupied_key in self.occupied:
                        actions.append(f'disconnect_M{module_idx+1}_P{port_idx+1}')
                        self.occupied.pop(occupied_key)
        print(actions)
        for action in actions:
            self.perform_action(action)
            time.sleep(.5)


if __name__ == "__main__":
    num_modules = 3
    dfa = DynamicDFA(num_modules)
    """
    dfa.perform_action('connect_M1_P2_M2_P4_O2')
    dfa.perform_action('connect_M2_P1_M3_P6_O1')
    dfa.perform_action('connect_M2_P1_M3_P6_O1')
    dfa.perform_action('disconnect_M2_P1')
    time.sleep(10)
    
    matrix_example = [[20, 0, 0],
                    [0, 0, 0],
                    [0, 14, 0]
    ]
    """
    while True:
        matrix = read_matrix_from_serial(port='/dev/cu.usbmodem144201', baudrate=9600)
        dfa.action_config_matrix(matrix)