from visualizer import ModularVisualizer
from readMatrix import read_matrix_from_serial
from modelChecker import run_model_checker
import time
import csv

from itertools import product, permutations

class stateGenerator:
    def __init__(self, num_modules):
        self.num_modules = num_modules
        self.states = set()  
        self.transitions = {}  
        self.current_state = None 
        self.define_connections()
        self.generate_states()
        self.occupied = {}
       
    def define_connections(self):
        self.femalePorts = ["P1", "P2", "P3"]
        self.malePorts = ["P4", "P5", "P6"]
        self.orientations = ["O1", "O2"]
       
    def generate_states(self):
        start_state = frozenset()
        self.states.add(start_state)
        self.current_state = start_state

        for num_connected in range(1, self.num_modules + 1):
            for modules in permutations(range(1, 1+self.num_modules), num_connected):
                modules = (0,) + modules  # Adds control module (0) to every state
                
                state_items = [[] for _ in range(len(modules)-1)]
                for i, module in enumerate(modules):
                    
                    # Generate all control module element in states
                    if i == 0:
                        for connections in product(self.femalePorts, self.orientations):
                            fPort, orientation = connections
                            next_module = modules[i + 1]
                            state_item = (f'M{next_module}_{fPort}', f'M0_P0_{orientation}')
                            state_items[i].append(state_item)

                    if i < len(modules) - 1 and i != 0:
                        for j in range(i):
                            for connections in product(self.malePorts, self.femalePorts, self.orientations):
                                mPort, fPort, orientation = connections
                                next_module = modules[i + 1]
                                state_item = (f'M{modules[i-j]}_{fPort}', f'M{next_module}_{mPort}_{orientation}')    
                                state_items[i].append(state_item) 
                             
                        for k in range(i):
                            for connections in product(self.malePorts, self.femalePorts, self.orientations):
                                mPort, fPort, orientation = connections
                                next_module = modules[i + 1]
                                state_item = (f'M{next_module}_{fPort}', f'M{modules[i-k]}_{mPort}_{orientation}')    
                                state_items[i].append(state_item) 

                for state_combination in product(*state_items):
                    connection_tracker = {}
                    valid_state = True

                    # Checks for duplicates on same connector
                    for item in state_combination:
                        for connection in item:
                            module_port = connection.split('_')
                            connection_key = (module_port[0], module_port[1])
                        
                            if connection_key in connection_tracker:
                                valid_state = False  # Duplicate found
                                break
                            connection_tracker[connection_key] = True 
                    

                    # Only add the state if it's valid (no duplicates)
                    if valid_state:
                        state = frozenset(state_combination)
                        if state not in self.states:
                            self.add_state(state)

                    state = frozenset(state_combination)
                    self.add_state(state)


                # Linear spatial states (ring formation)
                state_items = [[] for _ in range(len(modules))]
                for i, module in enumerate(modules):
                    if i == 0:
                        for fPort in ["P2", "P3"]:
                            state_item = (f'M{modules[i+1]}_{fPort}', f'M0_P0_O1')
                            state_items[i].append(state_item)
                            
                    if i < len(modules) - 1 and i != 0:
                        state_item = (f'M{modules[i+1]}_P1', f'M{modules[i]}_P4_O1')  
                        state_items[i].append(state_item)

                    # Attaches last module to port of the first to create a ring formation
                    if i == len(modules) - 1 and i > 1:
                        state_item = (f'M{modules[1]}_P1', f'M{modules[i]}_P4_O1') 
                        state_items[i].append(state_item)

                for state_combination in product(*state_items):
                    state = frozenset(state_combination)
                    self.add_state(state)

        # Generate transitions for each state
        for state in list(self.states):
            self.generate_transitions_for_state(state)

    def add_state(self, state, is_start=False):
        self.states.add(state)
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
            raise ValueError(f"Both from_state '{from_state}' and to_state '{to_state}' are not valid states.")
        
        self.transitions[(from_state, action)] = to_state

    #Generates all possible actions between states
    def generate_possible_actions(self):
        actions = []
        for i in range(self.num_modules):
            for connections in product(self.femalePorts, self.orientations):
                        fPort, orientation = connections
                        actions.append(f'connect_M{i+1}_{fPort}_M0_P0_{orientation}')
            for j in range(self.num_modules):
                if i != j:
                    for connections in product(self.malePorts, self.femalePorts, self.orientations):
                        mPort, fPort, orientation = connections
                        actions.append(f'connect_M{i+1}_{fPort}_M{j+1}_{mPort}_{orientation}')
            for fPort in self.femalePorts:
                actions.append(f'disconnect_M{i+1}_{fPort}')
        return actions
    

    #Applies possible actions to produce a new states
    def apply_action(self, state, action):
        state_dict = dict(state)
        parts = action.split('_')  
    
        if 'M0' in action:
            module, fPort, orient = parts[1], parts[2], parts[5]
            state_dict[f'{module}_{fPort}'] = f'M0_P0_{orient}'

        elif 'disconnect' in action:
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

                # 1 indicates the presence of the control module
                if val == 1:
                    if occupied_key not in self.occupied:
                        self.occupied[occupied_key] = True
                        actions.append(f'connect_M{module_idx+1}_P{port_idx+1}_M0_P0_O1')

                # Non-zero indicates an actuator is connected on that port
                elif val != 0:
                    if occupied_key not in self.occupied:
                        self.occupied[occupied_key] = True

                        # Decodes actuator number and port number
                        binary_val = format(val, '08b')
                        port_num = int(binary_val[-3:], 2)
                        module_num = int(binary_val[:5], 2)

                        actions.append(f'connect_M{module_idx+1}_P{port_idx+1}_M{module_num}_P{port_num}_O1')
                        print(f'M{module_idx+1}_P{port_idx+1}_M{module_num}_P{port_num}')
                else: 
                    # If status of port changes (value to zero), disconnect actuator 
                    if occupied_key in self.occupied:
                        actions.append(f'disconnect_M{module_idx+1}_P{port_idx+1}')
                        self.occupied.pop(occupied_key)

        print(actions)

        ## Ensures that control module is first action
        for action in actions:
            if "M0" in action:
                self.perform_action(action)
            time.sleep(.5)

        for action in actions:
            self.perform_action(action)
            time.sleep(.5)   
    
    def matrix_to_state(self, matrix):
        read_state = {}
        for module_idx, row in enumerate(matrix):
            for port_idx, val in enumerate(row):

                # 1 indicates the presence of the control module
                if val == 1:
                    read_state[f'M{module_idx+1}_P{port_idx+1}'] = f'M0_P0_O1'

                elif val != 0:
                    # Decodes actuator number and port number
                    binary_val = format(val, '08b')
                    port_num = int(binary_val[-3:], 2)
                    module_num = int(binary_val[:5], 2)

                    read_state[f'M{module_idx+1}_P{port_idx+1}'] = f'M{module_num}_P{port_num}_O1'

        return frozenset(read_state.items())
    
    def export_transitions(self, filename='transitions.csv'):
        # Prepare data 
        csv_data = []
        for (from_state, action), to_state in self.transitions.items():
            from_state_str = str(from_state)  # Convert frozenset to string
            to_state_str = str(to_state) 
            csv_data.append([from_state_str, action, to_state_str]) 

        with open(filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['From State', 'Action', 'To State'])  # header
            writer.writerows(csv_data) 

        print(f"Transitions exported to {filename}")


if __name__ == "__main__":
    num_modules = 2
    stateGen = stateGenerator(num_modules)
    #modelCheck = ModelChecker(stateGen.current_state, stateGen.transitions)
    stateGen.export_transitions()

    
    while True:
        initial_matrix = [[20, 0, 1],
                 [0,  0, 0],  # Actuator 2 
                  [0,  0, 0]    
        ]
        matrix = [[20, 1, 0],
                 [12,  0, 0],  # Actuator 2 
                  [0,  0, 0]    
        ]

        desired_state = stateGen.matrix_to_state(matrix)
        initial_state = stateGen.matrix_to_state(initial_matrix)

        run_model_checker(stateGen.transitions, initial_state, desired_state)
        #matrix = read_matrix_from_serial(port='/dev/cu.usbmodem14401', baudrate=9600)
        stateGen.action_config_matrix(matrix)
        time.sleep(10)