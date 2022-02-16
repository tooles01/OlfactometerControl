/*
  slave.ino
  
  Version:  0.2.0
  Author:   S.Toole
  
  Notes:    Update to communication strings. New string format allows multiple slave/vial updates with a single command.
            first two characters: receivedParam
            chars 3-last underscore: valueString
            last underscore-end: vialsToUpdate
*/

#include <Wire.h>
#include "config_slave.h"

volatile vialInfo arr_vials[numVials];

int slaveAddress;

String toSendNext = "";
int vialToSendNext;
String paramToSendNext = "";


void setup() {
  
  Serial.begin(baudrate);
  
  // GET SLAVE ADDRESS (from PCB dipswitches)
  slaveAddress = getSwitchValue();
  
  // SET UP I2C COMMUNICATION
  Wire.begin(slaveAddress);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);

  // POPULATE VIAL ARRAY (arr_vials)
  for (int i=0; i<numVials; i++) {
    arr_vials[i].vialNum = i+1;
    
    arr_vials[i].sensPin = sensPins[i];
    arr_vials[i].ctrlPin = ctrlPins[i];
    arr_vials[i].valvPin = valvPins[i];
    
    pinMode(arr_vials[i].sensPin, INPUT);
    pinMode(arr_vials[i].ctrlPin, OUTPUT);
    pinMode(arr_vials[i].valvPin, OUTPUT);

    
    // set prop. valve & isolation valve pins to low
    digitalWrite(arr_vials[i].ctrlPin, LOW);
    digitalWrite(arr_vials[i].valvPin, LOW);
    arr_vials[i].valveState = digitalRead(arr_vials[i].valvPin);
  }

  /*
  Serial.println("\n*****start*****\n");
  */
}

void loop() {
  for (int i=0; i<numVials; i++) {
    unsigned long currentTime = millis();
    
    if (arr_vials[i].valveState == HIGH) {
      if (currentTime >= arr_vials[i].timeToClose) {
        digitalWrite(arr_vials[i].valvPin,LOW);
        arr_vials[i].valveState = LOW;
        digitalWrite(arr_vials[i].ctrlPin, LOW);
        arr_vials[i].output = 0;
        arr_vials[i].PIDon = false;
      }
    }
    
    unsigned long prevTime = arr_vials[i].prevTime;
    unsigned long timeThatHasElapsed = currentTime - prevTime;
    if (timeThatHasElapsed >= timeToWait) {
      if (arr_vials[i].PIDon == true) {
        runPID(i);
      }
      else {
        arr_vials[i].flowVal = analogRead(arr_vials[i].sensPin);
      }
    }
  }
}

void runPID(int x) {
  int setpoint = arr_vials[x].setpoint;
  unsigned long prevTime = arr_vials[x].prevTime;
  int prevError = arr_vials[x].prevError;
  int prevOutput = arr_vials[x].prevOutput;
  int prevIntegral = arr_vials[x].integral;
  
  unsigned long currentTime = millis();
  int flowVal = analogRead(arr_vials[x].sensPin);
  int timeElapsed = currentTime - prevTime;
  int error = setpoint - flowVal;
  long integral = prevIntegral + (error * timeElapsed);
  int derivative = ((error - prevError) / timeElapsed);
  float Pterm = arr_vials[x].Kp * error;
  float Iterm = arr_vials[x].Ki * integral;
  float Dterm = arr_vials[x].Kd * derivative;
  float PIDoutput = Pterm + Iterm + Dterm;
  int output = prevOutput + PIDoutput;
  if (output >= 255.0)  { output = 255; }
  if (output <= 0.0)    { output = 0;   }
  analogWrite(arr_vials[x].ctrlPin, output);
  arr_vials[x].flowVal = flowVal;
  arr_vials[x].prevTime = currentTime;
  arr_vials[x].prevError = error;
  arr_vials[x].integral = integral;
  arr_vials[x].prevOutput = output;
  arr_vials[x].output = output;
}



void receiveEvent() {
  
  // READ STRING FROM MASTER
  String receivedStr = "";
  while (Wire.available()) {
    char inChar = Wire.read();
    receivedStr += inChar;
  }

  if (receivedStr[0] == 'V') {
    vialToSendNext = receivedStr[1];
    vialToSendNext = vialToSendNext-'0';  // convert to int
  }
  
  else {
    unsigned long timeReceived = millis();
    String receivedParam = "";

    // Parse receivedStr
    receivedParam += receivedStr[0];
    receivedParam += receivedStr[1];
    int lastUS_idx = receivedStr.lastIndexOf('_');    // find last underscore
    String valueString = receivedStr;
    valueString.remove(lastUS_idx);   // starting at last underscore, remove everything through the end
    valueString.remove(0,3);          // starting at index 0, remove 3 chars
    String vialsToUpdate = receivedStr;
    vialsToUpdate.remove(0,lastUS_idx+1); // starting at index 0, remove everything before last underscore
    
    int numVialsToUpdate = vialsToUpdate.length();
    for (int i=0; i<numVialsToUpdate;i++) {
      char vialNum = vialsToUpdate[i];  // get vial number
      int vialToUpdate = vialNum-'0';   // convert from char to int
      int vialIndex = vialToUpdate-1;
      
      arr_vials[vialIndex].timeReceived = timeReceived;
      int valueLength = valueString.length();
      
      if (receivedParam == "Kx") {
        int Pindex = valueString.indexOf('P');
        int Iindex = valueString.indexOf('I');
        int Dindex = valueString.indexOf('D');
        if (Pindex >=0) {
          String Pvalue = valueString;
          Pvalue.remove(0,Pindex+1);            // starting at index 0, remove everything before value
          int indexOfUS = Pvalue.indexOf('_');  // find next underscore (marks end of value)
          Pvalue.remove(indexOfUS);             // remove underscore and everything after
          float Kp = Pvalue.toFloat();
          arr_vials[vialIndex].Kp = Kp;
        }
        if (Iindex >=0) {
          String Ivalue = valueString;
          Ivalue.remove(0,Iindex+1);
          int indexOfUS = Ivalue.indexOf('_');
          Ivalue.remove(indexOfUS);
          float Ki = Ivalue.toFloat();
          arr_vials[vialIndex].Ki = Ki;
        }
        if (Dindex >=0) {
          String Dvalue = valueString;
          Dvalue.remove(0,Dindex+1);
          int indexOfUS = Dvalue.indexOf('_');
          Dvalue.remove(indexOfUS);
          float Kd = Dvalue.toFloat();
          arr_vials[vialIndex].Kd = Kd;
        }
      }
      else if (receivedParam == "Sp") {
        float newSetpoint = valueString.toFloat();
        arr_vials[vialIndex].setpoint = newSetpoint;
      }
      else if (receivedParam == "OV") {
        digitalWrite(arr_vials[vialIndex].valvPin, HIGH);
        arr_vials[vialIndex].valveState = HIGH;
        if (arr_vials[vialIndex].PIDon == false) {
          arr_vials[vialIndex].PIDon = true;
          arr_vials[vialIndex].prevTime = millis(); // need a time for the PID to start at
        }
  
        int lengthToOpen;
        if (valueLength > 0) {
          float lengthOpen_s = valueString.toFloat();
          float lengthOpen_ms = lengthOpen_s*1000;
          if (lengthOpen_ms < maxValveOpenTime) {
            lengthToOpen = lengthOpen_ms;
          }
          else {
            lengthToOpen = maxValveOpenTime;
          }
        }
        else {
          lengthToOpen = maxValveOpenTime;
        }
        arr_vials[vialIndex].timeToClose = millis() + lengthToOpen;
      }
      else if (receivedParam == "CV") {
        digitalWrite(arr_vials[vialIndex].valvPin, LOW);
        arr_vials[vialIndex].valveState = LOW;
      }
      else if (receivedParam == "ON") {
        arr_vials[vialIndex].PIDon = true;
        arr_vials[vialIndex].prevTime = millis();
      }
      else if (receivedParam == "OF") {
        arr_vials[vialIndex].PIDon = false;
      }
      else if (receivedParam == "OC") {
        analogWrite(arr_vials[vialIndex].ctrlPin,255);
        arr_vials[vialIndex].output = 255;
      }
      else if (receivedParam == "CC") {
        analogWrite(arr_vials[vialIndex].ctrlPin, 0);
        arr_vials[vialIndex].output = 0;
        arr_vials[vialIndex].PIDon = false;
      }
      else {
        Serial.print("receivedStr [ "); Serial.print(receivedStr);
        Serial.print("] contained unknown parameter ["); Serial.print(receivedParam); Serial.println("]");
      }
    
    }
  
  }
}

void requestEvent() {
  int i = vialToSendNext - 1;   // index of vial
  
  char vialnum[2];
  itoa(arr_vials[i].vialNum,vialnum,10);
  Wire.write(vialnum);
  
  int valueInt = arr_vials[i].flowVal;
  String valueStr = zeroPadInteger(valueInt);
  int valueCArrSize = valueStr.length() + 1;
  char valueCArr[valueCArrSize];
  valueStr.toCharArray(valueCArr,valueCArrSize);
  Wire.write(valueCArr);

  int ctrlInt = arr_vials[i].output;
  String ctrlStr = zeroPadInteger(ctrlInt);
  int ctrlCArrSize = ctrlStr.length() + 1;
  char ctrlCArr[ctrlCArrSize];
  ctrlStr.toCharArray(ctrlCArr,ctrlCArrSize);
  Wire.write(ctrlCArr);
  
  String blankString = "0000";
  int blankCArrSize = 5;
  char blankCArr[blankCArrSize];
  blankString.toCharArray(blankCArr,blankCArrSize);
  Wire.write(blankCArr);
}

String zeroPadInteger (int value) {
  String valString;
  
  if (value < 10) {valString = "000";}
  else if (value < 100) {valString = "00";}
  else if (value < 1000) {valString = "0";}
  valString += String(value);
  
  return valString;
}


int getSwitchValue() {
  
  // intialize switch pins to 5V
  digitalWrite(dipSwitch2, HIGH);
  digitalWrite(dipSwitch3, HIGH);
  digitalWrite(dipSwitch4, HIGH);
  
  // read switch values
  int sw2, sw3, sw4;              // doesn't matter if int or byte
  sw2 = digitalRead(dipSwitch2);
  sw3 = digitalRead(dipSwitch3);
  sw4 = digitalRead(dipSwitch4);
  
  // reverse them (easier for user to set this way)
  int bit2 = 1, bit3 = 1, bit4 = 1;
  if (sw2 == HIGH) bit2 = 0;
  if (sw3 == HIGH) bit3 = 0;
  if (sw4 == HIGH) bit4 = 0;
  
  String binaryStr = String(bit2) + String(bit3) + String(bit4);  // convert to string
  long binaryNum = binaryStr.toInt();                             // convert to int

  // convert from binary to decimal
  int decimalNum = convertBinaryToDecimal(binaryNum);
  
  return(decimalNum);
}

long convertBinaryToDecimal (long binary) {
  /*
   * Source: https://create.arduino.cc/projecthub/shreyas_arbatti/binary-to-decimal-converter-using-arduino-and-oled-display-3ce3c0?ref=part&ref_id=10308&offset=106
  */
  long number = binary;
  long decimalVal = 0;
  long baseVal = 1;
  long tempVal = number;
  long previousDigit;
  
  // Converts Binary to Decimal
  while (tempVal) {
    previousDigit = tempVal % 10;
    tempVal = tempVal / 10;
    decimalVal += previousDigit * baseVal;
    baseVal = baseVal * 2;
  }
  
  // Returns the Decimal number
  return decimalVal;
}
