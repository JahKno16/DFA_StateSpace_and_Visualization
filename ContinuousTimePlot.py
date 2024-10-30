import matplotlib.pyplot as plt
import numpy as np
import time
import csv

class TimePlot:
    def __init__(self):
        self.startTime = time.time()
        self.numModules = 5
        self.numPorts = 3
        self.portData = [[[] for _ in range(self.numPorts)] for _ in range(self.numModules)]
        
        self.timeData = [] 
        
        self.fig, self.ax = plt.subplots()
        self.legendTitles = np.array(["M1P1", "M1P2", "M1P3", "M2P1", "M2P2", "M2P3", "M3P1", "M3P2", "M3P3"])
        self.portsToDisplay = [0, 1, 2, 3, 4, 5, 6, 7, 8]

        self.lines = np.array([self.ax.plot([], [])[0] for _ in range(self.numModules * self.numPorts)])

        plt.ion() 

    def plotData(self, matrix):
        currentTime = time.time() - self.startTime
        self.timeData.append(currentTime)
    
        for module_idx, row in enumerate(matrix):
            for port_idx, val in enumerate(row):
                self.portData[module_idx][port_idx].append(val)
                line_idx = module_idx * self.numPorts + port_idx
                #if line_idx in self.portsToDisplay:
                self.lines[line_idx].set_xdata(self.timeData)
                self.lines[line_idx].set_ydata(self.portData[module_idx][port_idx])

        self.ax.relim() 
        self.ax.autoscale_view() 
        self.ax.legend(self.lines[self.portsToDisplay], self.legendTitles[self.portsToDisplay], loc="upper right")

        plt.draw()
        plt.pause(0.01)  # Pause for the plot to update (adjust as needed)


    def export_data(self, filename='outputData.csv'):
        csv_data = []
        for t_idx, t in enumerate(self.timeData):
            row = [t]
            for module_idx in range(self.numModules):
                for port_idx in range(3):
                    data = self.portData[module_idx][port_idx][t_idx]
                    row.append(data)
            csv_data.append(row)

        with open(filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Time"] + self.legendTitles.tolist())  # header
            writer.writerows(csv_data) 

        print(f"Transitions exported to {filename}")
    
       
    def finalPlot(self):
        for module_idx in range(self.numModules):
            for port_idx in range(self.numPorts):
                line_idx = module_idx * self.numPorts + port_idx
                self.lines[line_idx].set_xdata(self.timeData)
                self.lines[line_idx].set_ydata(self.portData[module_idx][port_idx])
        
        self.ax.relim() 
        self.ax.autoscale_view() 
        self.ax.legend(self.lines[self.portsToDisplay], self.legendTitles[self.portsToDisplay], loc="upper right")

        plt.draw()