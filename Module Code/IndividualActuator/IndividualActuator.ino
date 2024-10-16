#include <Wire.h>

// Actuator ID
#define ACTUATOR_ID 2

// Connector Pin Assignment
const int INPUT_PORTS[3] = {1, 2, 2};
const int OUTPUT_PORTS[3] = {8, 10, 10};

// Solenoid Pins
const int AIR_IN_PIN = 6;
const int AIR_OUT_PIN = 7;

// Connector Pins
const int lockPin = 3;
const int unlockPin = 9;

//Local version of current configuration matrix

volatile bool dataReceived = false;
volatile int receivedData = 0;

int inputData[3] = {0, 0, 0};
bool pairMode[3] = {false, false, false};
bool handShake[3] = {false, false, false};

bool connected[6] = {false, false, false, false, false, false};
bool temp_connect = false;

void setup() {
  Serial.begin(9600);
  Wire.begin(ACTUATOR_ID);
  Wire.onRequest(requestEvent);

  // Solenoid pin 
  pinMode(AIR_IN_PIN, OUTPUT);
  //digitalWrite(AIR_IN_PIN, HIGH);

  pinMode(lockPin, OUTPUT);
  pinMode(unlockPin, OUTPUT);

  digitalWrite(unlockPin, HIGH);
  delay(1000);
  digitalWrite(unlockPin, LOW);
}


void loop() {
  // Send data to each output port
  for (int i = 0; i < 3; i++) {
    readPorts(INPUT_PORTS[i], i);
    writePorts(OUTPUT_PORTS[i], i + 4, i); 
  }
  delay(100);

}


void writePorts(int port, int portNum, int idx) {
  
  if(connected[portNum-1]){
    pinMode(port, OUTPUT);
    digitalWrite(port, HIGH);
  }

  //Seaching for device on port
  pinMode(port, INPUT_PULLDOWN);
  attachInterrupt(digitalPinToInterrupt(port), pairingMode, CHANGE);

// Check to see if actuator should go into pairing mode
  if(pairMode[idx] == true){
    detachInterrupt(digitalPinToInterrupt(port));

    //Send handshake data 
    pinMode(port, OUTPUT);
    digitalWrite(port, HIGH);
    delay(10);
    digitalWrite(port, LOW);
    pinMode(port, INPUT_PULLDOWN);

    int startTime = millis();
    Serial.print("In pairing mode on port ");
    Serial.println(port);

    while(digitalRead(port) == LOW){
      if(millis() - startTime > 1500){
        pairMode[idx] = false;
        return;
      }
    }

  pinMode(port, OUTPUT);
  delay(200);

  //Combine port number and actuator data
  int data = (portNum & 0x07) | ((ACTUATOR_ID & 0x1F) << 3); 
  Serial.print("Sending data: ");
  Serial.println(data);

  //Send data bitwise
  for (int i = 0; i < 8; i++) {
    digitalWrite(port, (data & (1 << i)) ? HIGH : LOW);
    delay(150); 
  }

    digitalWrite(port, LOW);
    pairMode[idx] = false;
   }
}

void readPorts(int port, int idx) {

    if(digitalRead(port) == HIGH){
      connected[idx] = true;
      return;
    } else{
      connected[idx] = false;
    }

    if(connected[idx] == false){
      pinMode(port, OUTPUT);
      digitalWrite(port, HIGH);
      delay(10);
      digitalWrite(port, LOW);

      pinMode(port, INPUT_PULLDOWN);
      attachInterrupt(digitalPinToInterrupt(port), handshake, CHANGE);
      delay(200);

      if(handShake[idx]){
          detachInterrupt(digitalPinToInterrupt(port));
          receivedData = 0;
          for (int j = 0; j < 8; j++) { 
            if (digitalRead(port) == HIGH) {
              receivedData |= (1 << j);
            }
          delay(150);

        if(temp_connect == false){
           for(int i = 0; i < 15; i++) {
              analogWrite(unlockPin, 50);
              delay(75);
              analogWrite(unlockPin, 0);
              digitalWrite(lockPin, HIGH);
              delay(150);
              digitalWrite(lockPin, LOW);
            }
            delay(1500);
            //digitalWrite(lockPin, HIGH);
            //temp_connect = true;
        }
      } 

        handShake[idx] = false;
        decodeData(receivedData);
        inputData[idx] = receivedData;
      }
      /*
    else{
      inputData[idx] = 0;
    }
    */
    }
}

void pairingMode() {
  for(int i = 0; i < 3; i++){
    if(digitalRead(OUTPUT_PORTS[i]) == HIGH){
      pairMode[i] = true;
      Serial.print("Pairing mode started on port: ");
      Serial.println(4+i);
    }
  }
}

//Run when receiver detects handshake signal
void handshake() {
  for(int i = 0; i < 3; i++){
    if(digitalRead(INPUT_PORTS[i]) == HIGH){
      handShake[i] = true;
      Serial.print("Handshake read on port ");
      Serial.println(i+1);
    }
  }
}

void decodeData(int data){
  int connectorNumber = data & 0x07; // Lower 3 bits are connector number
  int actuatorID = (data >> 3) & 0x1F; // Upper 5 bits are actuator ID

    Serial.print("Received data - Actuator ID: ");
    Serial.print(actuatorID);
    Serial.print(", Connector Number: ");
    Serial.println(connectorNumber);
}


void requestEvent() {
  Wire.write(ACTUATOR_ID); // Send the actuator ID first
  for (int i = 0; i < 3; i++) {
    Serial.println(inputData[i]);
    Wire.write(inputData[i]); // Send each data in the array
  }
}


