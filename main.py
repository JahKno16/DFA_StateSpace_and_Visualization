import csv
from send_commands import sendCommands
from modelChecker import run_model_checker
from visualizer import ModularVisualizer
from ContinuousTimePlot import TimePlot
from readMatrix import read_matrix_from_serial
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
        
            #visualizer = ModularVisualizer()
            #visualizer.visualize_configuration(self.current_state)
        else:
            print(f"No valid transition from state '{self.current_state}' on action '{action}'")

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

    plot = TimePlot()

    serial_port = '/dev/cu.usbmodem14401'
    command = sendCommands(modules=5, port=serial_port, baudrate=9600)

    initial_matrix = [[0, 1, 0],
                    [0,  0, 0],  
                    [12,  0, 0]    
        ]
    
    desired_matrix = [[20, 1, 0],
                    [0,  0, 0],  
                    [0,  0, 0]    
        ]

    desired_state = dfa.matrix_to_state(desired_matrix)
    initial_state = dfa.matrix_to_state(initial_matrix)

    verified, states, actions = run_model_checker(dfa.transitions, initial_state, desired_state)


    for idx, action in enumerate(actions):      # Iterates over all actions defined by model checker
        commandSent = False

        while True:     # Waits for action to be completed
            matrix = read_matrix_from_serial(port=serial_port, baudrate=9600)  ## Reads current Matrix
            current_state = dfa.matrix_to_state(matrix)    #Converts matrix to a state

            if commandSent == False:    # Only send command to control module once
                time.sleep(.5)
                command.write_actions_matrix(action)    # Sends "command matrix"
                commandSent = True
            
            if current_state == states[idx]:   # Continue to next action once state has been reached
                break
               
            plot.plotData(matrix)      ## Plots data read on ports from matrix over time
            time.sleep(1)
            
    plot.export_data()         ## Once complete, export the readData vs time csv

        
       