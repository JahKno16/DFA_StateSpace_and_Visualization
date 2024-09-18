import serial

def read_matrix_from_serial(port='/dev/cu.usbmodem144201', baudrate=9600, rows=5, cols=4):
    ser = serial.Serial(port, baudrate)
    config_matrix = []
    while True:
        if ser.in_waiting >= 0:
            # Read a line from the serial port
            line = ser.readline().decode('utf-8').strip()
            if line:
                # Split the line by commas to get individual elements
                row = list(map(int, line.split(',')))
                config_matrix.append(row)
                
                # Break when we have the complete matrix
                if len(config_matrix) == rows:
                    break
    return config_matrix

if __name__ == '__main__':
    matrix = read_matrix_from_serial()
    print(matrix)