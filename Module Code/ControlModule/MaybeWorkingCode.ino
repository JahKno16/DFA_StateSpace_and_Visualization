#include <Wire.h>

// Constants
#define NUM_INPUT_PORTS 3 
#define MAX_ACTUATORS 5

const int port = 6;
bool pairMode = false;

bool present = false;

int configurationMatrix[MAX_ACTUATORS][NUM_INPUT_PORTS]; 

void setup() {
  Serial.begin(9600);
  Wire.begin(); //Master
}

void loop() {
  //Assume no actuators are present
  present = false;

  //Request configuration data from Actuators by ID
  for (int actuatorID = 1; actuatorID <= MAX_ACTUATORS; actuatorID++) {
    requestData(actuatorID);
    delay(200); 
  }

  //If no actuators are present, send zero matrix
  if (present == false){
    zeroMatrix(); 
  }

  send_matrix();

  // Print the configuration matrix
  //printConfigurationMatrix();

  writePorts(port, 1);
  delay(500); 
}

void requestData(int actuatorID) {
  Wire.requestFrom(actuatorID, 1+NUM_INPUT_PORTS); 

  if (Wire.available()) {
    int receivedActuatorID = Wire.read(); 
    if (receivedActuatorID != actuatorID) {
      Serial.print("Warning: Expected actuator ID ");
      Serial.print(actuatorID);
      Serial.print(" but received ");
      Serial.println(receivedActuatorID);
      return;
    }

    for (int i = 0; i < NUM_INPUT_PORTS; i++) {
      if (Wire.available()) {
        int data = Wire.read();
        configurationMatrix[receivedActuatorID - 1][i] = data; 
      }
      present = true;
    }
  }
   

    /*
    // Print received data
    Serial.print("Received data from actuator ");
    Serial.print(receivedActuatorID);
    Serial.print(": ");
    for (int i = 0; i < NUM_INPUT_PORTS; i++) {
      Serial.print(configurationMatrix[receivedActuatorID - 1][i]);
      Serial.print(" ");
    }
    Serial.println();
    */
}

void printConfigurationMatrix() {
  Serial.println("Configuration Matrix:");
  for (int i = 0; i < MAX_ACTUATORS; i++) {
    Serial.print("Actuator ");
    Serial.print(i + 1);
    Serial.print(": ");
    for (int j = 0; j < NUM_INPUT_PORTS; j++) {
      Serial.print(configurationMatrix[i][j]);
      Serial.print(" ");
    }
    Serial.println();
  }
}

void send_matrix(){
  // Send the matrix to the serial port
  for (int i = 0; i < MAX_ACTUATORS; i++) {
    for (int j = 0; j < NUM_INPUT_PORTS; j++) {
      Serial.print(configurationMatrix[i][j]);
      if (j < NUM_INPUT_PORTS-1) {
        Serial.print(",");  // Separate elements by commas
      }
    }
    Serial.println();  // Newline at the end of each row
  }
  
  delay(100);  
}

void writePorts(int port, int id) {
  //Seaching for device on port
  pinMode(port, INPUT_PULLDOWN);
  attachInterrupt(digitalPinToInterrupt(port), pairingMode, CHANGE);

// Check to see if actuator should go into pairing mode
  if(pairMode == true){
    detachInterrupt(digitalPinToInterrupt(port));

    //Send handshake data 
    pinMode(port, OUTPUT);
    digitalWrite(port, HIGH);
    delay(10);
    digitalWrite(port, LOW);
    pinMode(port, INPUT_PULLDOWN);

    int startTime = millis();

    while(digitalRead(port) == LOW){
      if(millis() - startTime > 5000){
        pairMode = false;
        return;
      }
    }

  pinMode(port, OUTPUT);
  delay(200);

  //Send data bitwise
  for (int i = 0; i < 8; i++) {
    digitalWrite(port, (id & (1 << i)) ? HIGH : LOW);
    delay(150); 
  }

    digitalWrite(port, LOW);
    pairMode = false;
   }
}

void pairingMode() {
    if(digitalRead(port) == HIGH){
      pairMode = true;
  }
}

void zeroMatrix() {
   // Set all values to zero using nested loops
  for (int i = 0; i < MAX_ACTUATORS; i++) {
    for (int j = 0; j < NUM_INPUT_PORTS; j++) {
      configurationMatrix[i][j] = 0;
    }
  }
}