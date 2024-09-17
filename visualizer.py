import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.transforms import Affine2D
import numpy as np
import time

class ModularVisualizer:
    def __init__(self):
        self.w, self.l = 0.6, 1.2  # Unit width and length
        self.portPos = {
            'P1': (self.w/2, 0), "P2": (0, self.l / 4),
            "P3": (0, 3 * self.l / 4), "P4": (self.w/2, self.l),
            "P5": (self.w, 3 * self.l / 4), "P6": (self.w, self.l / 4)
        }
        plt.ion()

    def visualize_configuration(self, state):
        plt.close()
        fig, ax = plt.subplots()

        module_pos = {}  # Stores the positions and orientations of modules
        for i, connection in enumerate(state):
            element1, element2 = connection
            parts = element1.split('_') + element2.split('_')  # ['M1', 'P1', 'M2', 'P5', 'O1']

            # Determine which module is already defined
            moduleA, portA, moduleB, portB = parts[0], parts[1], parts[2], parts[3]

            if moduleA in module_pos:
                moduleA_pos = module_pos[moduleA]
                # Module A is already positioned, calculate position for module B
                moduleB_pos, orientationB, portB = self.calculate_position(moduleA_pos, portA, portB)
                module_pos[moduleB] = (*moduleB_pos, orientationB)
                self.draw_module(ax, module_pos[moduleB], moduleB, portB)
            elif moduleB in module_pos:
                # If module B is defined, calculate position for module A
                moduleB_pos = module_pos[moduleB]
                moduleA_pos, orientationA, portA = self.calculate_position(moduleB_pos, portB, portA)
                module_pos[moduleA] = (*moduleA_pos, orientationA)
                self.draw_module(ax, module_pos[moduleA], moduleA, portA)
            else:
                # Neither moduleA nor moduleB is defined, start with moduleA at (0, 0)
                if i == 0:
                    module_pos[moduleA] = (0, 0, 0)  # Start at (0, 0)
                    self.draw_module(ax, module_pos[moduleA], moduleA, (0,0))
                
                # Calculate position for moduleB relative to moduleA
                moduleA_pos = module_pos[moduleA]
                moduleB_pos, orientationB, portB = self.calculate_position(moduleA_pos, portA, portB)
                module_pos[moduleB] = (*moduleB_pos, orientationB)
                self.draw_module(ax, module_pos[moduleB], moduleB, portB)

        ax.set_xlim(-3, 3)
        ax.set_ylim(-3, 3)
        plt.gca().set_aspect('equal', adjustable='box')
        
        ax.figure.canvas.draw()
        ax.figure.canvas.flush_events()
        plt.pause(0.1)
        

    def draw_module(self, ax, pos, module, port):
        x, y, orientation = pos
        width, height = self.w, self.l
        port_dx, port_dy = port
        # Create rectangle patch
        rect = patches.Rectangle((x, y), width, height, edgecolor='blue', facecolor='lightblue')

        # Apply rotation transformation
        
        if orientation == 1:
            t = Affine2D().rotate_deg_around(x + port_dx, y + port_dy, 90) + ax.transData
            rect.set_transform(t)

            rect.set_xy((x, y))

            ax.add_patch(rect)
            #for port, (dx, dy) in self.portPos.items():
                #ax.text(x - dy + , y + dx + port_dx, port, ha='center', va='center', fontsize=8)
            #ax.text(x - width + port_dy, y + height / 2 + port_dx, module, ha='center', va='center')
        
        else:
            ax.add_patch(rect)
            for port, (dx, dy) in self.portPos.items():
                ax.text(x +  dx, y + dy, port, ha='center', va='center', fontsize=8)
            ax.text(x +  width / 2 , y + height / 2 , module, ha='center', va='center')


    def calculate_position(self, moduleA_pos, portA, portB):
        xA, yA, orientationA = moduleA_pos
        # Get the relative position of portA on module A
        portAPos = np.array(self.portPos[portA])

        # Get the relative position of portB on module B
        portBPos = np.array(self.portPos[portB])

        # Calculate the position of module B
        moduleB_pos = np.array([xA, yA]) + (portAPos - portBPos)

        # Determine if module B should be rotated
        orientationB = orientationA
        if (portA == 'P1' and portB in ['P5', 'P6']) or (portB == 'P4' and portA in ['P2', 'P3']) or (portA == 'P4' and portB in ['P2', 'P3']):
            orientationB = 1 - orientationA  # Flip module 
            print(orientationB)

        return moduleB_pos, orientationB, portBPos

if __name__ == "__main__":
    # Example usage:
    visualizer = ModularVisualizer()
    state = [('M1_P1', 'M2_P4_O1') , ('M2_P1', 'M3_P5_O1')]
    visualizer.visualize_configuration(state)
    time.sleep(20)

    #M1_P1_M2_P4
# M3_P2_M1_P4