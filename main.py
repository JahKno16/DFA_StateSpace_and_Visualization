import csv
from visualizer import ModularVisualizer
import time

class DFA:
    def __init__(self, start_state = frozenset()):
        self.current_state = start_state
        self.transitions = {}
        self.occupied = {}

    def import_transitions(self, filename='transitions.csv'):
        self.transitions.clear()

        with open(filename, mode='r') as file:
            reader = csv.reader(file)
            header = next(reader) 

            for row in reader:
                from_state_str = row[0] 
                action = row[1]          
                to_state_str = row[2]   

                from_state = eval(from_state_str)
                to_state = eval(to_state_str)  

                self.transitions[(from_state, action)] = to_state

        print(f"Transitions imported from {filename}")

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
        for action in actions:
            self.perform_action(action)
            time.sleep(.5)


if __name__ == "__main__":
    dfa = DFA()
    dfa.import_transitions()

    while True:
        matrix_example = [[1, 0, 0],
                    [0, 12, 0],
                    [0, 0, 28]
        ]
        ##matrix = read_matrix_from_serial(port='/dev/cu.usbmodem14401', baudrate=9600)
        dfa.action_config_matrix(matrix_example)
        time.sleep(10)
       