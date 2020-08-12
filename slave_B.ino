// ST 2020
// slave_B.ino

#include <Wire.h>
#include <C:\Users\shann\Dropbox\OlfactometerEngineeringGroup\Control\software\github repo\config_master.h>
#include <C:\Users\shann\Dropbox\OlfactometerEngineeringGroup\Control\software\github repo\config_slave.h>

const int slaveIndex = 1;
const int slaveAddress = slaveAddresses[slaveIndex];
const int numVials = vialsPerSlave[slaveIndex];

volatile vialInfo arr_vials[numVials];

void setup() {
  Wire.begin(slaveAddress);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);
  Serial.begin(baudrate);
  
  for (int i=0; i<numVials; i++) {
    arr_vials[i].vialNum = i+1;
    arr_vials[i].sensPin = sensPins[i];
    arr_vials[i].ctrlPin = ctrlPins[i];
    arr_vials[i].valvPin = valvPins[i];
    pinMode(arr_vials[i].sensPin, INPUT);
    pinMode(arr_vials[i].ctrlPin, OUTPUT);
    pinMode(arr_vials[i].valvPin, OUTPUT);
  }
  
  for (int i=0; i<numVials; i++) {
    digitalWrite(arr_vials[i].valvPin, LOW);
    digitalWrite(arr_vials[i].ctrlPin, 0);
    arr_vials[i].valveState = digitalRead(arr_vials[i].valvPin);
  }
  Serial.println("\n*****start*****\n");
}

void loop() {
  for (int i=0; i<numVials; i++) {
    unsigned long currentTime = millis();
    if (arr_vials[i].valveState == HIGH) {
      unsigned long timeToClose = arr_vials[i].timeToClose;
      if (currentTime >= timeToClose) {
        digitalWrite(arr_vials[i].valvPin,LOW);
        arr_vials[i].valveState = LOW;
      }
    }
    
    unsigned long prevTime = arr_vials[i].prevTime;
    unsigned long timeThatHasElapsed = currentTime - prevTime;
    if (timeThatHasElapsed >= timeToWait) {
      if (arr_vials[i].PIDon == true) { runPID(i); }
      else { arr_vials[i].flowVal = analogRead(arr_vials[i].sensPin); }
    }
  }
}

void runPID(int x) {
  int currentVal = analogRead(arr_vials[x].sensPin);
  arr_vials[x].flowVal = currentVal;
  unsigned long currentTime = millis();
  int setpoint = arr_vials[x].setpoint;
  unsigned long prevTime = arr_vials[x].prevTime;
  int prevIntegral = arr_vials[x].integral;
  int prevError = arr_vials[x].prevError;
  int prevOutput = arr_vials[x].output;
  int timeElapsed = currentTime - prevTime;  // in seconds
  int error = setpoint - currentVal;
  unsigned long integral = prevIntegral + (error * timeElapsed);
  int derivative = ((error - prevError) / timeElapsed);
  float Pterm = arr_vials[x].Kp * error;
  float Iterm = arr_vials[x].Ki * integral;
  float Dterm = arr_vials[x].Kd * derivative;
  float PIDoutput = Pterm + Iterm + Dterm;
  int output = prevOutput + PIDoutput;
  if (output >= 255.0)  { output = 255; }
  if (output <= 0.0)    { output = 0;   }
  analogWrite(arr_vials[x].ctrlPin, output);
  // PRINT TO SERIAL (for debugging)
  /*
  char data[1000];
  //Serial.print("t:"); Serial.print(currentTime);  Serial.print("\t");
  sprintf(data,"Sp: %d\t\t",setpoint);  Serial.print(data);
  sprintf(data,"Fl: %d\t\t",currentVal);  Serial.print(data);
  Serial.print("tEl: "); Serial.print(timeElapsed);  Serial.print("\t");
  Serial.print("error: ");  Serial.print(error);  Serial.print("\t");
  Serial.print("P: ");  Serial.print(Pterm);  Serial.print("\t");
  Serial.print("Ki: "); Serial.print(arr_vials[x].Ki);  Serial.print("\t");
  Serial.print("in: ");  Serial.print(integral); Serial.print("\t\t"); 
  Serial.print("I: ");  Serial.print(Iterm);  Serial.print("\t\t");
  //Serial.print("PID: ");  Serial.print(PIDoutput);  Serial.print("\t\t"); 
  Serial.print("ctrl: ");   Serial.print(output);
  Serial.println();
  */
  arr_vials[x].prevTime = currentTime;
  arr_vials[x].prevError = error;
  arr_vials[x].integral = integral;
  arr_vials[x].output = output;
}


int vialToSendNext;

void receiveEvent() {
  String receivedStr = "";
  while (Wire.available()) {
    char inChar = Wire.read();
    receivedStr += inChar;
  }
  
  char firstChar = receivedStr[0];
  if (firstChar == 'V') {
    vialToSendNext = receivedStr[1];
    vialToSendNext = vialToSendNext-'0';  // convert to int
  }
  
  else {
    //Serial.print("\nreceived string: ");  Serial.println(receivedStr);
    unsigned long timeReceived = millis();
    String receivedParam = "";
    String valueString = "";
    char vial2Update = receivedStr[1];
    receivedParam += receivedStr[3];
    receivedParam += receivedStr[4];
    int vialToUpdate = vial2Update-'0'; // convert to int from char
    int vialIndex = vialToUpdate-1;
    valueString = receivedStr;
    valueString.remove(0,6);    // starting at index 0, remove 5 chars (everything before actual value)
    
    arr_vials[vialIndex].timeReceived = timeReceived;
    int valueLength = valueString.length();
    int valvPin = arr_vials[vialIndex].valvPin;
    
    if (receivedParam == "Ge") {
      char data[1000];
      sprintf(data, "\n\n~~ vial %d current status ~~", vialToUpdate);  Serial.println(data);
      sprintf(data,"Sp:\t%d",arr_vials[vialIndex].setpoint); Serial.println(data);
      Serial.print("Kp:\t");  Serial.println(arr_vials[vialIndex].Kp,5);
      Serial.print("Ki:\t");  Serial.println(arr_vials[vialIndex].Ki,5);
      Serial.print("Kd:\t");  Serial.println(arr_vials[vialIndex].Kd,5);
      sprintf(data,"PID on?\t%d",arr_vials[vialIndex].PIDon); Serial.println(data);
      sprintf(data,"flow:\t%d",arr_vials[vialIndex].flowVal); Serial.println(data);
      sprintf(data,"ctrl:\t%d",arr_vials[vialIndex].output);  Serial.println(data);
      Serial.print("Pterm:\t"); Serial.println(arr_vials[vialIndex].Kp*arr_vials[vialIndex].prevError);
      Serial.print("Iterm:\t"); Serial.println(arr_vials[vialIndex].Ki*arr_vials[vialIndex].integral);

      bool valveState = arr_vials[vialIndex].valveState;
      Serial.print("valve open?\t");  Serial.println(valveState);
      if (valveState == HIGH) {
        Serial.print("\tcurrent time:\t\t"); Serial.println(timeReceived);
        Serial.print("\tvalve close time:\t");  Serial.println(arr_vials[vialIndex].timeToClose);
        Serial.print("\t"); Serial.print(arr_vials[vialIndex].timeToClose - timeReceived); Serial.println(" ms remaining");
      }
    }
    else if (receivedParam == "Kx") {
      int Pindex = valueString.indexOf('P');
      int Iindex = valueString.indexOf('I');
      int Dindex = valueString.indexOf('D');
      if (Pindex >=0) {
        String Pvalue = valueString;
        Pvalue.remove(0,Pindex+1);            // starting at index 0, remove everything before value
        int indexOfUS = Pvalue.indexOf('_');  // find next underscore (marks end of value)
        Pvalue.remove(indexOfUS);             // remove underscore and everything after
        float Kp = Pvalue.toFloat();
        Serial.print("updating Kp to ");  Serial.println(Kp,5);
        arr_vials[vialIndex].Kp = Kp;
      }
      if (Iindex >=0) {
        String Ivalue = valueString;
        Ivalue.remove(0,Iindex+1);
        int indexOfUS = Ivalue.indexOf('_');
        Ivalue.remove(indexOfUS);
        float Ki = Ivalue.toFloat();
        Serial.print("updating Ki to ");  Serial.println(Ki,5);
        arr_vials[vialIndex].Ki = Ki;
      }
      if (Dindex >=0) {
        String Dvalue = valueString;
        Dvalue.remove(0,Dindex+1);
        int indexOfUS = Dvalue.indexOf('_');
        Dvalue.remove(indexOfUS);
        float Kd = Dvalue.toFloat();
        Serial.print("updating Kd to ");  Serial.println(Kd,5);
        arr_vials[vialIndex].Kd = Kd;
      }
    }
    else if (receivedParam == "Sp") {
      float newSetpoint = valueString.toFloat();  // convert to float
      arr_vials[vialIndex].setpoint = newSetpoint;
    }
    else if (receivedParam == "OV") {
      digitalWrite(valvPin, HIGH);
      arr_vials[vialIndex].valveState = HIGH;
      if (valueLength >= 0) {
        arr_vials[vialIndex].PIDon = true;
        float lengthOpen_s = valueString.toFloat();
        float lengthOpen_ms = lengthOpen_s*1000;
        unsigned long timeToClose = timeReceived + lengthOpen_ms;
        arr_vials[vialIndex].timeToClose = timeToClose;
        arr_vials[vialIndex].prevTime = millis(); // need a time for the PID to start at 
      }
    }
    else if (receivedParam == "ON") {
      arr_vials[vialIndex].PIDon = true;
      arr_vials[vialIndex].prevTime = millis();
    }
    else if (receivedParam == "OF") {
      arr_vials[vialIndex].PIDon = false;
    }
    
    else if (receivedParam == "CV") {
      digitalWrite(valvPin, LOW);
      arr_vials[vialIndex].valveState = LOW;
    }
    else if (receivedParam == "OC") {
      int ctrlPin = arr_vials[vialIndex].ctrlPin;
      analogWrite(ctrlPin, 255);
      arr_vials[vialIndex].output = 255;
    }
    else if (receivedParam == "CC") {
      int ctrlPin = arr_vials[vialIndex].ctrlPin;
      analogWrite(ctrlPin, 0);
      arr_vials[vialIndex].output = 0;
      arr_vials[vialIndex].PIDon = false;
    }
    else {
      Serial.print("receivedStr [ "); Serial.print(receivedStr);
      Serial.print("] contained unknown parameter ["); Serial.print(receivedParam); Serial.println("]");
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
