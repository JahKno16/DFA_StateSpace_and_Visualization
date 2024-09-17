import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations, product

class DynamicDFA():
    def __init__(self, num_modules):
        self.num_modules = num_modules
        self.states = set()  # Set of all states
        self.transitions = {}  # Dictionary of transitions between states
        self.graph = nx.DiGraph()  # Directed graph to visualize the DFA
        self.current_state = None  # Start state
        self.define_connections()
        self.generate_state()
       

    def define_connections(self):
        self.femalePorts = ["P1", "P2", "P3"]
        self.malePorts = ["P4", "P5", "P6"]
        self.orientations = ["O1", "O2"]
        self.connection_points = [f"{f}_{m}_{o}" for m in self.malePorts for f in self.femalePorts for o in self.orientations]
        # print(self.connection_points)

    def generate_state(self):
        start_state = frozenset()
        self.states.add(start_state)
        self.current_state = start_state

        # Generate all possible states
        for num_connected in range(1, self.num_modules):
            for modules in combinations(range(self.num_modules), num_connected+1):
                print(modules)
                for config in product(self.connection_points, modules, repeat=num_connected):
                    state = frozenset(zip(modules, config))
                    self.add_state(state)
        
        # Generate states for control module connections
        for m in range(1, self.num_modules + 1):
            for orientation in self.orientations:
                for cp in self.femalePorts:
                    state_items = [(f'C', f'{m+1}_{cp}_{orientation}')]
                    state = frozenset(state_items)
                    self.add_state(state)
        print(self.states)

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


    def generate_possible_actions(self):
        actions = []
        for i in range(self.num_modules):
            for j in range(self.num_modules):
                if i != j:
                    for cp in self.connection_points:
                        actions.append(f'connect_{i+1}_{j+1}_{cp}')
                    actions.append(f'disconnect_{i+1}_{j+1}')

        for i in range(self.num_modules):
            for cp in self.femalePorts:
                for orientation in self.orientations:
                    action = f'connect_C_{orientation}_{i+1}_{cp}'
                    actions.append(action)
            actions.append(f'disconnect_C_{i+1}')
        # print(actions)
        return actions
    

    def apply_action(self, state, action):
        state_dict = dict(state)
        parts = action.split('_')
        # print(parts)

        if "disconnect" in action:
            #i, j = int(parts[1]), int(parts[2])
            #state_dict.pop(i, None)
            if parts[1] == 'C':  # Control module disconnect
                module = int(parts[2]) 
                state_dict.pop(f'C', None)
            else:  # Module-to-module disconnect
                i, j = int(parts[1]), int(parts[2]) 
                state_dict.pop(f'M{i}', None)

        elif "connect" in action:
            if parts[0] == 'connect' and parts[1] == 'C':  # Control module connection
                orientation = parts[2]
                module = int(parts[3])  # Extract module number
                cp = parts[3]  # Connection point
                state_dict[f'C'] = f'M{module}_{cp}_{orientation}'
            else:  # Module-to-module connection
                i, j = int(parts[1]), int(parts[2]) # Extract module numbers
                cp = parts[2]
                state_dict[f'M{i}'] = f'M{j}_{cp}'
        
        return frozenset(state_dict.items())


    def perform_action(self, action):
        if self.current_state is None:
            raise ValueError("Start state is not set.")
        
        if (self.current_state, action) in self.transitions:
            new_state = self.transitions[(self.current_state, action)]
            print(f"Transitioning from {self.current_state} to {new_state} on action '{action}'")
            self.current_state = new_state
            # self.draw_graph()  # Update visualization
        else:
            print(f"No valid transition from state '{self.current_state}' on action '{action}'")


    def draw_graph(self):
        """
        Draw the current state of the DFA graph using NetworkX and Matplotlib.
        """
        plt.figure(figsize=(10, 6))
        pos = nx.spring_layout(self.graph)  # Positioning the nodes
        
        # Draw the nodes and labels
        nx.draw(self.graph, pos, with_labels=True, node_color='lightblue', font_size=10, node_size=500)
        
        # Highlight the current state
        nx.draw_networkx_nodes(self.graph, pos, nodelist=[self.current_state], node_color='orange')
        
        # Draw the edges with labels
        edge_labels = nx.get_edge_attributes(self.graph, 'label')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_color='red')
        
        plt.title(f"Current State: {self.current_state}")
        plt.show()

    def visualize_configuration(self):
        plt.figure(figsize=(10,6))
        


# Example usage
num_modules = 3
dfa = DynamicDFA(num_modules)

"""
# Manually add states
dfa.add_state('S0', is_start=True)  # Start state
dfa.add_state('S1')
dfa.add_state('S2')
dfa.add_state('S3')

# Manually define transitions, with reset loops
dfa.add_transition('S0', 'connect_A_B', 'S1')
dfa.add_transition('S1', 'disconnect_A_B', 'S2')
dfa.add_transition('S2', 'flip_A', 'S3')
dfa.add_transition('S3', 'connect_B_C', 'S1')
dfa.add_transition('S1', 'reset', 'S1', reset=True)  # Reset transition for state S1
"""
# Perform actions to test the DFA and visualize the graph
dfa.perform_action('connect_C_1_P1_O1')
dfa.perform_action('connect_1_4_P1_P4_O1')  # This should loop back to S1
#dfa.perform_action('disconnect_A_B')
#dfa.perform_action('flip_A')


for num_connected in range(1, self.num_modules + 1):
            for modules in permutations(range(self.num_modules), num_connected):
                # Generate all possible connections for the given set of modules
                # print(modules)
                for i, module in enumerate(modules):
                    for connections in product(self.malePorts, self.femalePorts, self.orientations):
                        mPort, fPort, orientation = connections
                        states_items = []
                        for i, module in enumerate(modules):
                            if i < len(modules) - 1:
                                # Connect this module with the next module in the list
                                next_module = modules[i + 1]
                                state_item = (f'M{module + 1}_{fPort}', f'M{next_module + 1}_{mPort}_{orientation}')
                                states_items.append(state_item)   
                    if states_items:
                        print(state_item)
                        state = frozenset(states_items)
                        self.add_state(state)
                    