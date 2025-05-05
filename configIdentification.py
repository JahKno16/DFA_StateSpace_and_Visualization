### This is not yet implimented or complete. This wil be used for identifying what configuration the system is in a provide
# a set of commands for control. 

## Configurations to include: Crawler, Pipe Climbing Robot, Rolling Cylinder, ManusBot, TendrilBot

import json

class ModularRobotController:
    def __init__(self):
        self.CONFIG_TEMPLATES = {
            "walker_5": {
                "structure": {
                    "center": {"connections": 4},
                    "P3": "frontL_leg",
                    "P5": "frontR_leg",
                    "P2": "backL_leg",
                    "P6": "backR_leg"
                },
                "control_sequence": {
                    "forward": [
                        {"time": 0.0, "actions": {"frontL_leg": {"inflate": 1}}},
                        {"time": 0.0, "actions": {"frontR_leg": {"inflate": 1}}},
                        {"time": 1.0, "actions": {"center": {"inflate": 1}}},
                        {"time": 2.0, "actions": {"frontL_leg": {"inflate": 0}}},
                        {"time": 2.0, "actions": {"frontR_leg": {"inflate": 0}}},
                        {"time": 2.0, "actions": {"backL_leg": {"inflate": 1}}},
                        {"time": 2.0, "actions": {"backR_leg": {"inflate": 1}}},
                        {"time": 3.0, "actions": {"backL_leg": {"inflate": 0}}},
                        {"time": 3.0, "actions": {"backR_leg": {"inflate": 0}}},
                        {"time": 3.0, "actions": {"center": {"inflate": 0}}}
                ]
                }
            },
            "climbing_6": {
                "structure": {
                    "center": {"connections": 2},
                    "P3": "frontL_leg",
                    "P5": "frontR_leg",
                    "P2": "backL_leg",
                    "P6": "backR_leg"
                },
                "control_sequence": {
                    "upward" : [
                        {"time": 0.0, "actions": {"frontL_leg": {"inflate": 1}}},
                        {"time": 0.5, "actions": {"backR_leg": {"inflate": 1}}},
                        {"time": 1.0, "actions": {"frontL_leg": {"inflate": 0}}},
                        {"time": 1.5, "actions": {"backR_leg": {"inflate": 0}}},
                        {"time": 2.0, "actions": {"disconnect": "backR_leg"}}
                ]
                }
            },
            "roller_4": {
                "structure": {
                    "center": {"connections": 4},
                    "P3": "roll2",
                    "P4": "roll3",
                    "P2": "roll4",
                    "P1": "roll3"
                },
                "control_sequence": {
                    "roll_forward": [
                        {"time": 0.0, "actions": {"center": {"inflate": 1}}},
                        {"time": 0.5, "actions": {"roll2": {"inflate": 1}}},
                        {"time": 1.0, "actions": {"center": {"inflate": 0}}},
                        {"time": 1.0, "actions": {"roll3": {"inflate": 1}}},
                        {"time": 1.5, "actions": {"roll2": {"inflate": 0}}},
                        {"time": 1.5, "actions": {"roll4": {"inflate": 1}}},
                        {"time": 2.0, "actions": {"roll3": {"inflate": 0}}},
                        {"time": 2.0, "actions": {"roll4": {"inflate": 0}}},
                        {"time": 2.5, "actions": {"disconnect": {"module": "roll4", "port": "P2"}}},
                        {"time": 3.0, "actions": {"connect": {"from": "center", "to": "roll4", "port": "P2"}}}
                    ]
                }
            }
        }

        self.transition_state = {}
        self.connections = {}
        self.center_module = None
        self.current_config_name = None

    def parse_transition_system(self, transitions):
        self.transition_state = transitions
        self.connections = {}

        for key, value in transitions.items():
            module_a, port_a = key[:2], key[2:]
            module_b, port_b, orientation = value[:2], value[2:4], value[4:]

            if module_a not in self.connections:
                self.connections[module_a] = {}
            if module_b not in self.connections:
                self.connections[module_b] = {}

            self.connections[module_a][port_a] = module_b
            self.connections[module_b][port_b] = module_a


    def find_center_unit(self):
        possible_centers = []
        for module, ports in self.connections.items():
            num_connections = len(ports)
            if num_connections >= 3:
                possible_centers.append((module, num_connections))

        possible_centers.sort(key=lambda x: -x[1])
        self.center_module = possible_centers[0][0] if possible_centers else None
        return self.center_module


    def identify_configuration(self):
        if not self.center_module:
            self.find_center_unit()

        if not self.center_module:
            return None

        neighbor_count = len(self.connections[self.center_module])

        for name, template in self.CONFIG_TEMPLATES.items():
            expected = template["structure"]["center"]["connections"]
            if expected == neighbor_count:
                self.current_config_name = name
                return name

        return None

    def assign_roles(self):
        if not self.current_config_name:
            self.identify_configuration()

        template = self.CONFIG_TEMPLATES[self.current_config_name]
        structure = template["structure"]

        role_map = {self.center_module: "center"}
        center_ports = self.connections[self.center_module]
        assigned_roles = {}

        for port, connected_module in center_ports.items():
            if port in structure:
                role = structure[port]
                if role in assigned_roles:
                    if assigned_roles[role] != connected_module:
                        raise ValueError(f"Conflict: Role {role} maps to multiple actuators: {assigned_roles[role]} and {connected_module}")
                else:
                    role_map[connected_module] = role
                    assigned_roles[role] = connected_module
        return role_map

    def generate_timed_sequence(self):
        role_map = self.assign_roles()
        template = self.CONFIG_TEMPLATES[self.current_config_name]
        sequence = template.get("control_sequence", [])
        result = []

        for step in sequence:
            time = step["time"]
            actions = []

            for role, command in step["actions"].items():
                if role == "disconnect":
                    target_id = next((k for k, v in role_map.items() if v == command), None)
                    if target_id:
                        actions.append({"action": "disconnect", "target": target_id})
                elif role in role_map:
                    actuator_id = next((k for k, v in role_map.items() if v == role), None)
                    if actuator_id:
                        actions.append({"actuator": actuator_id, **command})

            result.append({"time": time, "actions": actions})

        return result

    def export_control_sequence_as_json(self, filepath="control_sequence.json"):
        sequence = self.generate_timed_sequence()
        command_list = []

        for step in sequence:
            for action in step["actions"]:
                if "inflate" in action:
                    command = {
                        "time": step["time"],
                        "command": "inflate" if action["inflate"] else "deflate",
                        "target": action["actuator"]
                    }
                elif action.get("action") == "disconnect":
                    command = {
                        "time": step["time"],
                        "command": "disconnect",
                        "target": action["target"]
                    }
                else:
                    continue

                command_list.append(command)

        with open(filepath, "w") as f:
            json.dump(command_list, f, indent=2)
        print(f"✅ Exported control sequence to {filepath}")
