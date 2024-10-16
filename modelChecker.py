#Nick Pagliocca
#This code finds the reachable states of the transition system, then given a state see if it is reachable from all states in the transition system.

import csv
from collections import defaultdict, deque
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

State = frozenset
Action = str
TransitionFunction = Callable[[State], List[Tuple[Action, State]]]
PropertyFunction = Callable[[State], bool]

class ModelChecker:
    def __init__(self, 
                 initial_states: Set[State], 
                 transitions: Dict[State, List[Tuple[Action, State]]]):
        self.initial_states = initial_states
        self.transitions = transitions

    def _reconstruct_path(self, 
                          state: State, 
                          predecessors: Dict[State, Optional[State]], 
                          actions: Dict[State, Action]) -> List[Tuple[State, Action]]:
        path = []
        while state is not None:
            action = actions.get(state, None)
            path.append((state, action))
            state = predecessors[state]
        path.reverse()
        return path

    def check_reachability(self, desired_state: State) -> Tuple[bool, Optional[List[Tuple[State, Action]]]]:
        visited: Set[State] = set()
        queue: deque = deque()
        predecessors: Dict[State, Optional[State]] = {}
        actions: Dict[State, Action] = {}  # To track actions leading to each state

        # Initialize the queue with initial states
        for state in self.initial_states:
            queue.append(state)
            visited.add(state)
            predecessors[state] = None

        #Run through the rest
        while queue:
            current_state = queue.popleft()

            # Check if we have reached the desired state
            if current_state == desired_state:
                path = self._reconstruct_path(current_state, predecessors, actions)
                return True, path

            # Expand the current state to its successors
            for action, successor in self.transitions.get(current_state, []):
                if successor not in visited:
                    visited.add(successor)
                    queue.append(successor)
                    predecessors[successor] = current_state
                    actions[successor] = action  # Record the action that led to this successor

        return False, None

    def find_all_reachable_states(self) -> Dict[State, int]:
        visited: Set[State] = set()
        queue: deque = deque()
        distances: Dict[State, int] = {}  # Store distance to each state

        # Initialize the queue with initial states
        for state in self.initial_states:
            queue.append(state)
            visited.add(state)
            distances[state] = 0  # Distance to initial states is 0

        while queue:
            current_state = queue.popleft()
            current_distance = distances[current_state]

            # Expand the current state to its successors
            for action, successor in self.transitions.get(current_state, []):
                if successor not in visited:
                    visited.add(successor)
                    queue.append(successor)
                    distances[successor] = current_distance + 1  # Increment distance for successor

        return distances
    
def run_model_checker(transitions, initial_states, desired_state, printStat = True):

    # Initialize the model checker
    checker = ModelChecker(initial_states, transitions)

    # Find all reachable states and their distances from the desired state
    reachable_set = checker.find_all_reachable_states()
  
    # Check reachability of the desired state from the initial states
    reachable, path_to_desired = checker.check_reachability(desired_state)

    # Now check reachability for each reachable state
    for state, distance in reachable_set.items():
        reachable_from_state, path_to_desired = checker.check_reachability(desired_state)
        if not reachable_from_state:
            print(f"The desired state {desired_state} is NOT reachable from state {state} ...")
            exit()
        
    verified = True
     

    state_Path = []
    action_Path = []
    if reachable:
        if printStat == True:
            print('All states in reach(TS) satisfy the property!')
            print('There are', len(reachable_set), ' reachable states in the TS from the initial state.')
            print(f"The desired state {desired_state} is reachable from the initial states.")
            print("Path to desired state (state, action):")

        for state, action in path_to_desired:
            if action is not None:  # Filter out the None actions for the initial state
                state_Path.append(state)
                action_Path.append(action)
                if printStat == True:
                    print(f"State: {state}, Action: {action}")
    else:
        print(f"The desired state {desired_state} is not reachable from the initial states.")
        exit()


    return verified,state_Path, action_Path 

def load_data(file_path):
    """This function loads in the pre-defined state transitions. The file path is passed in main."""
    from_states = []
    actions = []
    to_states = []

    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip the header
        
        for row in csv_reader:
            from_state = row[0]
            to_state = row[2]
            
            # Only add the row if the pre- and post- are different
            if from_state != to_state:
                from_states.append(from_state)
                actions.append(row[1])
                to_states.append(to_state)

    return from_states, actions, to_states

# Test
if __name__ == "__main__":

    csv_file_path = 'transitions.csv'
    from_states, actions, to_states = load_data(csv_file_path)
    if 1: #Print number of lines loaded:
        print(f"Loaded {len(from_states)} transition relations.")

    # Create transition relation dictionary from transitions.csv
    transitions = defaultdict(list)
    for from_state, action, to_state in zip(from_states, actions, to_states):
        transitions[frozenset(eval(from_state))].append((action, frozenset(eval(to_state))))

    # Define initial state (I \subseteq S)
    initial_states = {
        frozenset({('M2_P2', 'M1_P4_O2'), ('M1_P1', 'M0_P0_O1')})  
    }

    
    # Test Cases for desired states
    desired_state = frozenset({('M2_P2', 'M1_P4_O2'), ('M1_P1', 'M0_P0_O1')})  #Sanity check: does it equal the initial
    desired_state = frozenset({ ('M1_P1', 'M0_P0_O1')}) #Detach module 2
    #desired_state = frozenset({('M2_P2', 'M1_P4_O2'), ('M1_P1', 'M0_P0_O2')}) #Move Module 0 to other orientation (appears that some states we have are not nessasrilly possible)
    #desired_state = frozenset({('M2_P1', 'M1_P4_O2'), ('M1_P1', 'M0_P0_O1')})#More complex reconifiguration

 
    verified, state_Path, action_Path  = run_model_checker(transitions, initial_states, desired_state, printStat = True)


