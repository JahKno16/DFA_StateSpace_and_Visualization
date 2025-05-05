#include <Wire.h>

// Actuator ID
#define ACTUATOR_ID 1

// Connector Pin Assignment
const int INPUT_PORTS[3] = {1, 2};
const int OUTPUT_PORTS[3] = {8, 9};

// Solenoid Pins
const int AIR_IN_PIN = 6;
const int AIR_OUT_PIN = 7;

// Connector Pins
const int lock1Pin = 10;
const int unlock1Pin = 3;

// Bending Sensor Pin
const int bendPin = 0;

//Local version of current configuration matrix

volatile bool dataReceived = false;
volatile int receivedData = 0;

int incomingMatrix[3];

int angle = 0;
int inputData[3] = {0, 0, 0};
bool pairMode[3] = {false, false, false};
bool handShake[3] = {false, false, false};

bool connected[6] = {false, false, false, false, false, false};

void setup() {
  Serial.begin(9600);
  Wire.begin(ACTUATOR_ID);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);

  // Bending Sensor
  pinMode(bendPin, INPUT);

  // Solenoid pin 
  pinMode(AIR_IN_PIN, OUTPUT);
  digitalWrite(AIR_IN_PIN, HIGH);

  pinMode(lock1Pin, OUTPUT);
  pinMode(unlock1Pin, OUTPUT);

  digitalWrite(unlock1Pin, HIGH);
  delay(1000);
  digitalWrite(unlock1Pin, LOW);
}


void loop() {
  /*
  // Read and Write each port (1, 2, 4, 5)
  for (int i = 0; i < 2; i++) {
    readPorts(INPUT_PORTS[i], i);
    writePorts(OUTPUT_PORTS[i], i + 4, i);
    Serial.println(inputData[i]); 
    delay(50);
  }
  conditionCode(); 
  */

  /*readAngle();
  Serial.println(angle);
  */
  //disconnect(1);
  //delay(5000);
  //disconnect(1);
  //delay(5000);
  delay(50);
}


void writePorts(int port, int portNum, int idx) {
  if(connected[portNum-1]){
    pinMode(port, OUTPUT);
    digitalWrite(port, HIGH);
    Serial.print("Port 4 connected");
  }

  else{
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
    Serial.println(idx + 4);

    Serial.println("Entering Paring Mode");
    while(digitalRead(port) == LOW){
      if(millis() - startTime > 5000){
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
}

void readPorts(int port, int idx) {
    if(digitalRead(port) == HIGH){
      connected[idx] = true;
      detachInterrupt(digitalPinToInterrupt(port));
      return;

    } else {
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

      if(handShake[idx] && receivedData == 0){
          Serial.println("Receiving...");
          detachInterrupt(digitalPinToInterrupt(port));
          receivedData = 0;
          for (int j = 0; j < 8; j++) { 
            if (digitalRead(port) == HIGH) {
              receivedData |= (1 << j);
            }
            delay(150);
          }
          connect(port);
          if (int(receivedData) == 5){
            receivedData == 20;
          }
          inputData[idx] = receivedData;
      } /*else {
            int startTime = millis();
            while(digitalRead(port) == LOW){
              if(millis() - startTime > 5000){
                inputData[idx] = 0;
            }
          }
      }*/
      handShake[idx] = false;
        //decodeData(receivedData);
    
    }
}

void pairingMode() {
  for(int i = 0; i < 3; i++){
    if(digitalRead(OUTPUT_PORTS[i]) == HIGH){
      pairMode[i] = true;
    }
  }
}

//Run when receiver detects handshake signal
void handshake() {
  for(int i = 0; i < 3; i++){
    if(digitalRead(INPUT_PORTS[i]) == HIGH && connected[i] == false){
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

void readAngle(){
  int bendValue = analogRead(bendPin);
  angle = map(bendValue, 0, 1023, 0, 180);
}


void connect(int port){
  switch (port){
    case 1:
      for(int i = 0; i < 10; i++) {
        analogWrite(unlock1Pin, 50);
        delay(75);
        analogWrite(unlock1Pin, 0);
        analogWrite(lock1Pin, 1023);
        delay(150);
        analogWrite(lock1Pin, 0);
      }
      break;
    default:
      break;
}
}

void disconnect(int port){
  switch (port){
    case 1:
      for(int i = 0; i < 10; i++) {
        analogWrite(lock1Pin, 150);
        delay(75);
        analogWrite(lock1Pin, 0);
        analogWrite(unlock1Pin, 1023);
        delay(150);
        analogWrite(unlock1Pin, 0);
      }
      break;
    default:
      break;
  }
}

void requestEvent() {
  Wire.write(ACTUATOR_ID); // Send the actuator ID first
  for (int i = 0; i < 3; i++) {
    Serial.println(inputData[i]);
    Wire.write(inputData[i]); // Send each data in the array
  }
}

void receiveEvent(int numByte){
  int i = 3;
  while (Wire.available()) {
    int readData = Wire.read();
    if (readData == 1) {
      connected[i] = true;
    } else {
      connected[i] = false;
    }
    i++;
  }
}


void conditionCode(){
  if(connected[0] == true && connected[3] == true && ACTUATOR_ID == 3){
    Serial.println("Disconnecting");
    disconnect(1);
  }
}