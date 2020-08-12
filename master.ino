need // ST 2020
// master.ino

#include <Wire.h>
#include <C:\Users\shann\Dropbox\OlfactometerEngineeringGroup\Control\software\github repo\config_master.h>

typedef struct {
  char slaveName;
  int slaveAddress;
  int numVials;
  
  String mode = "normal";
  int prevRequestTime;
} slaveInfo;


slaveInfo arr_slaves[numSlaves];

void setup() {
  Wire.begin();
  Serial.begin(baudrate);
  Serial.setTimeout(50);   // max # of ms to wait for serial data in readString
                           //  -> this is how quickly we can send multiple commands in a row from the python GUI without it blending them all together
  for (int i=0;i<numSlaves;i++) {
    arr_slaves[i].slaveName = slaveNames[i];
    arr_slaves[i].numVials = vialsPerSlave[i];
    arr_slaves[i].slaveAddress = slaveAddresses[i];
  }
}

void loop() {
  
  if (Serial.available()) {
    String inString = Serial.readString();         // read string from serial
    parseSerial(inString);
  }
  
  else {
    for (int x=0;x<numSlaves;x++) {      
      unsigned long currentTime = millis();
      int prevRequestTime = arr_slaves[x].prevRequestTime;
      int timeSinceLast = currentTime-prevRequestTime;
      
      if (timeSinceLast >= timeBetweenRequests) {
        arr_slaves[x].prevRequestTime = currentTime;
        requestData(x);
      }
    }
  }
  //int outputFlow = analogRead(A7);
  //Serial.print("MM");
  //Serial.print(outputFlow);
}

void parseSerial(String inString) {
  int strLen = inString.length();
  char firstChar = inString[0];
  
  if (firstChar == 'M') {
    char ardUpdate = inString[1];
    String param = inString;
    param.remove(0,3);   // starting at 0, remove first 3 chars
    String value = param;
    int USidx = param.indexOf('_'); // find underscore
    param.remove(USidx);            // remove everything from there on
    value.remove(0,USidx+1);        // starting at 0, remove USidx # of chars
    
    if (ardUpdate == 'M') {
      if (param.indexOf("timebt")>=0) {
        timeBetweenRequests = value.toFloat();
      }
    }
    
    else {
      int slaveIndex;
      for (int p=0;p<numSlaves;p++) {
        if (ardUpdate == slaveNames[p]) {
          slaveIndex = p;
          if (param.indexOf("debug")>=0) {
            arr_slaves[slaveIndex].mode = "debug";
          }
          else if (param.indexOf("normal")>=0) {
            arr_slaves[slaveIndex].mode = "normal";
          }
          else {
            // do nothing
          }
        }
      }
    }
  }
    
  else {
    int slaveToSendTo;
    int cArrSize = strLen+1;
    char charArr[cArrSize];
    inString.toCharArray(charArr,cArrSize); // convert to char array for sending
    for (int p=0;p<numSlaves;p++) {
      if (firstChar == slaveNames[p]) {
        slaveToSendTo = slaveAddresses[p];
      }
    }
    Wire.beginTransmission(slaveToSendTo);
    Wire.write(charArr);
    Wire.endTransmission();
  }
}

void requestData(int x) {
  int slaveName = arr_slaves[x].slaveName;
  int slaveAddress = arr_slaves[x].slaveAddress;
  int numVials = arr_slaves[x].numVials;
  int numChars = 3;
  int numBytesToReq = 13;
  
  for (int vialNum=1;vialNum<=numVials;vialNum++) {
    String strSend = "V";
    strSend += String(vialNum);
    char strSend_[numChars];
    strSend.toCharArray(strSend_,numChars);
    
    Wire.beginTransmission(slaveAddress);
    Wire.write(strSend_);
    Wire.endTransmission();
    
    Wire.requestFrom(slaveAddress,numBytesToReq,true);
    switch (slaveName) {
      case 'A': Serial.print("A");  break;
      case 'B': Serial.print("B");  break;
    }
    for (int a=0;a<numBytesToReq;a++) {
      char fromSlave = Wire.read();
      Serial.print(fromSlave);
    }
    Serial.println();
  }
}
