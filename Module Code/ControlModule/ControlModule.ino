#include <Wire.h>

// Constants
#define NUM_INPUT_PORTS 3 
#define MAX_ACTUATORS 5

const int port = 6;   //Digital ID Pin
bool pairMode = false;  
bool controlPresent = false;
bool present = false;

int configurationMatrix[MAX_ACTUATORS][NUM_INPUT_PORTS]; 

void setup() {
  Serial.begin(9600);
  Wire.begin(); //Master
}

void loop() {
  //Assume no actuators are present
  present = false;
  writePorts(port, 1);

  //Request configuration data from Actuators by ID
  for (int actuatorID = 1; actuatorID <= MAX_ACTUATORS; actuatorID++) {
    requestData(actuatorID);
    delay(200); 
  }

  //If no actuators are present, send zero matrix
  if (present == false){
    zeroMatrix(); 
  }

  updateConfigArrays();
  send_matrix();

  // Print the configuration matrix
  //printConfigurationMatrix();
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
  
  // If module does not respond, set all ports to 0
  else {
     for (int i = 0; i < NUM_INPUT_PORTS; i++) {
        configurationMatrix[actuatorID - 1][i] = 0; 
      }
  }
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


void updateConfigArrays(){
   int configMatrix[MAX_ACTUATORS][3] = {0};
   controlPresent = false;

   for (int i = 0; i < MAX_ACTUATORS; i++) {
    for (int j = 0; j < NUM_INPUT_PORTS; j++) {
      int value = configurationMatrix[i][j];
      int portID = value & 0x07; // Lower 3 bits are connector number
      int actuatorID = (value >> 3) & 0x1F;

      if (value != 0 && value != 1){
        configMatrix[actuatorID-1][portID - 4] = 1;
      }
      else {
        configMatrix[actuatorID-1][portID - 4] = 0;
      }

      if (value == 1){
        controlPresent = true;
      } 
    }
   }
       
    for (int ID = 1; ID <= MAX_ACTUATORS; ID++){
        Wire.beginTransmission(ID);
        for(int port_idx = 0; port_idx < 3; port_idx++){
          int connectedState = configMatrix[ID - 1][port_idx];
          Wire.write(connectedState);
          Serial.print(connectedState);
        }
        Wire.endTransmission(); 
        Serial.print("Updating Matrix");
    }
  
}


void writePorts(int port, int id) {
  if (controlPresent == true){
    pinMode(port, OUTPUT);
    digitalWrite(port, HIGH);
    Serial.print("We are High");

  } else {
  Serial.print("We are NOT high");
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
      if(millis() - startTime > 2000){
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
    pairMod