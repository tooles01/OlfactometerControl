// ST 2020
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
    String inString = Serial.readString();
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
  
}

void parseSerial(String inString) {
  int strLen = inString.length();
  char firstChar = inString[0];
  
  if (firstChar == 'M') {
    char secChar = inString[1];
    
    String param = inString;  param.remove(0,3);   // starting at 0, remove first 3 chars
    String value = param;
    
    int USidx = param.indexOf('_'); // find underscore
    param.remove(USidx);            // remove everything from underscore to end
    value.remove(0,USidx+1);        // starting at 0, remove everything up to & including underscore
    
    if (secChar == 'M') {
      if (param.indexOf("timebt")>=0) {
        timeBetweenRequests = value.toFloat();
      }
    }
    
    else {
      for (int p=0;p<numSlaves;p++) {
        if (secChar == arr_slaves[p].slaveName) {
          if (param.indexOf("debug")>=0) {
            arr_slaves[p].mode = "debug";
          }
          else if (param.indexOf("normal")>=0) {
            arr_slaves[p].mode = "normal";
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
      if (firstChar == arr_slaves[p].slaveName) {
        slaveToSendTo = arr_slaves[p].slaveAddress;
      }
    }
    Wire.beginTransmission(slaveToSendTo);
    Wire.write(charArr);
    Wire.endTransmission();
  }
}

void requestData(int x) {
  char slaveName = arr_slaves[x].slaveName;
  int slaveAddress = arr_slaves[x].slaveAddress;
  int numVials = arr_slaves[x].numVials;
  int numBytesToReq = 13;
  
  for (int vialNum=1;vialNum<=numVials;vialNum++) {
    String strSend = "V" + String(vialNum);
    int numChars = strSend.length() + 1;
    char strSend_[numChars];
    strSend.toCharArray(strSend_,numChars);
    
    Wire.beginTransmission(slaveAddress);
    Wire.write(strSend_);
    Wire.endTransmission();
    
    Wire.requestFrom(slaveAddress,numBytesToReq,true);
    Serial.print(slaveName);
    /*
    switch (slaveName) {
      case 'A': Serial.print("A");  break;
      case 'B': Serial.print("B");  break;
    }
    */
    for (int a=0;a<numBytesToReq;a++) {
      char fromSlave = Wire.read();
      Serial.print(fromSlave);
    }
    Serial.println();
  }
}
