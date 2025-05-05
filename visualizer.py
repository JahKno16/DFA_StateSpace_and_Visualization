import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.transforms import Affine2D
import numpy as np
import time

class ModularVisualizer:
    def __init__(self):
        self.w, self.l = 0.6, 1.2  # Unit width and length
        self.w_C, self.l_C = 0.6, 0.3
        self.portPos = {
            'P1': (self.w/2, 0), "P2": (0, self.l / 4),
            "P3": (0, 3 * self.l / 4), "P4": (self.w/2, self.l),
            "P5": (self.w, 3 * self.l / 4), "P6": (self.w, self.l / 4),
            "P0": (self.w_C/2, self.l_C)
        }
        plt.ion()
      

    def visualize_configuration(self, state):
        plt.close()
        fig, ax = plt.subplots()
        plt.axis('off')
        
        #Draws control module for initial state (control is always present)
        if state == frozenset():
            module_pos = {"M0": (-self.w_C/2, -2, 0)}  
            self.draw_module(ax, module_pos["M0"], 'M0', 'P0')

        module_pos = {} 
        for i, connection in enumerate(state):
            element1, element2 = connection
            parts = element1.split('_') + element2.split('_')  # ['M1', 'P1', 'M2', 'P5', 'O1']

            # Determine which module is already defined
            moduleA, portA, moduleB, portB = parts[0], parts[1], parts[2], parts[3]

            if "M0" in [moduleA, moduleB] and i == 0:
                module_pos = {"M0": (-self.w_C / 2, -2, 0)}  
                self.draw_module(ax, module_pos["M0"], 'M0', 'P0')
            
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

        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)
        plt.gca().set_aspect('equal', adjustable='box')
        
        ax.figure.canvas.draw()
        ax.figure.canvas.flush_events()
        plt.pause(0.2)
        

    def draw_module(self, ax, pos, module, port):
        x, y, orientation = pos
        width, height = self.w, self.l
        port_dx, port_dy = port
      
        # Create rectangle patch
        if module == "M0":
            rect = patches.Rectangle((x, y), self.w_C, self.l_C, edgecolor='black', facecolor='yellow')
        else:
            rect = patches.Rectangle((x, y), width, height, edgecolor='black', facecolor='lightblue')

        # Apply rotation transformation

        if orientation == 1:

            ##Temp
            #rect = patches.Rectangle((x, y), width, height, edgecolor='black', facecolor='lightgray')
            ####

            t = Affine2D().rotate_deg_around(x + port_dx, y + port_dy, self.flip) + ax.transData
            rect.set_transform(t)

            rect.set_xy((x, y))

            ax.add_patch(rect)
            #for port, (dx, dy) in self.portPos.items():
                #ax.text(x - dy + , y + dx + port_dx, port, ha='center', va='center', fontsize=8)
            ax.text(x + self.x_label_offset, y + self.y_label_offset, module, fontsize=20, ha='center', va='center')
        
        else:
            if module != "M0":
                ax.add_patch(rect)
                #for port, (dx, dy) in self.portPos.items():
                    #ax.text(x +  dx, y + dy, port, ha='center', va='center', fontsize=8, color='black')
                ax.text(x +  width / 2 , y + height / 2, module, ha='center', va='center', fontsize=20)
            else:
                ax.add_patch(rect)
                ax.text(x +  self.w_C / 2 , y + self.l_C / 2 - .04, "M0", ha='center', va='center', fontsize=20)


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

        if (portA == 'P1' and portB in ['P5', 'P6']): 
            self.x_label_offset, self.y_label_offset =  3/2*self.w, self.w
            self.flip = 90
            orientationB = 1 - orientationA  # Flip module
        
        if (portA == 'P4' and portB in ['P2', 'P3']) or (portA == 'P0' and portB in ['P2', 'P3']):
            self.flip = 90
            self.x_label_offset, self.y_label_offset =  -self.w/2, self.w
            orientationB = 1 - orientationA  # Flip module
                
        if (portB == 'P4' and portA in ['P2', 'P3']):
            self.flip = -90
            self.x_label_offset, self.y_label_offset =  -self.w/2, self.l
            orientationB = 1 - orientationA  # Flip module
        
        if(portB == 'P1' and portA in ['P5', 'P6']):
            self.flip = -90
            self.x_label_offset, self.y_label_offset =  3/2*self.w, 0
            orientationB = 1 - orientationA  # Flip module
        
        return moduleB_pos, orientationB, portBPos

if __name__ == "__main__":
    # Example usage:
    visualizer = ModularVisualizer()
    state = [('M1_P1', 'M0_P0_O1') , ('M1_P2', 'M2_P4_O1')]
    visualizer.visualize_configuration(state)
    time.sleep(20)
