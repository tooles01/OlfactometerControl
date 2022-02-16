/*
  master.ino
  
  Version:  0.2.1
  Author:   S.Toole
  
  Notes:    Update to communication strings. New string format allows multiple slave/vial updates with a single command.
            First character: 'M' indicates master settings update. 'S' indicates data to send to slave
*/

#include <Wire.h>
#include "config_master.h"


typedef struct {
  int vialNum;
  String mode = "debug";  
} vialInfo;

typedef struct {
  char slaveName;
  int slaveAddress;
  int numVials;
  vialInfo vials[vialsPerSlave];    // set this just for creating all the structs
  
  String mode = "normal"; // get rid of this
  int prevRequestTime;
} slaveInfo;

slaveInfo arr_slaves[numSlaves];  // array of slaveInfo objects

void setup() {
  Wire.begin();
  Serial.begin(baudrate);
  Serial.setTimeout(30);   // max # of ms to wait for serial data in readString
                           //  -> this is how quickly we can send multiple commands in a row from the python GUI without it blending them all together
  for (int i=0;i<numSlaves;i++) {
    // populate with stuff from config file
    arr_slaves[i].slaveName = slaveNames[i];
    arr_slaves[i].numVials = vialsPerSlave;//[i];
    arr_slaves[i].slaveAddress = slaveAddresses[i];
    //Serial.print("slaveName: ");  Serial.println(slaveNames[i]);
    //Serial.print("\tnumVials: ");   Serial.println(vialsPerSlave[i]);

    int numVials = vialsPerSlave;//[i];
    // don't create new array, just modify the one that's there
    for (int j=0;j<vialsPerSlave;j++) {
      int vialNum = j+1;
      arr_slaves[i].vials[j].vialNum=vialNum;
      if (vialNum > numVials) {
        arr_slaves[i].vials[j].mode = "null"; // if it is more than the thing has, set mode to null
      }
      //Serial.print("\t\tvialNum: ");  Serial.print(arr_slaves[i].vials[j].vialNum);
      //Serial.print("\tmode: "); Serial.println(arr_slaves[i].vials[j].mode);
    }
    
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
  char firstChar = inString[0];
  
  if (firstChar == 'M') {
    char secChar = inString[1];
    
    String param = inString;  param.remove(0,3);   // starting at 0, remove first 3 chars
    String value = param;
    
    int USidx = param.indexOf('_'); // find underscore
    param.remove(USidx);            // remove everything from underscore to end
    value.remove(0,USidx+1);        // starting at 0, remove everything up to & including underscore

    // master parameter
    if (secChar == 'M') {
      if (param.indexOf("timebt")>=0) {
        timeBetweenRequests = value.toFloat();
      }
    }
    
    else {
      if (secChar == 'S') {
        // parse out parameter
        String paramToSend = inString;
        int us_idx = paramToSend.indexOf('_');       paramToSend.remove(0,us_idx+1);
        int us_Lidx = paramToSend.lastIndexOf('_');  paramToSend.remove(us_Lidx);

        // get list of vials to send this to
        int lastUS_idx = inString.lastIndexOf('_');
        String vialList = inString;
        vialList.remove(0,lastUS_idx+1);

        // for each slave
        for (int s=0;s<numSlaves;s++) {
          char slaveName = arr_slaves[s].slaveName;
          int s_idx = vialList.indexOf(slaveName);
  
          // if slaveName is in vialList
          if (s_idx!=-1) {
            
            // get vial numbers
            String thisSlaveVials = vialList;
            // if it's not the last slave
            if (s!=numSlaves-1) {
              int ns_idx;
              for (int ns=s+1;ns<numSlaves;ns++) {
                char ns_name = arr_slaves[ns].slaveName;
                ns_idx = thisSlaveVials.indexOf(ns_name);
                if (ns_idx!=-1) {
                  thisSlaveVials.remove(ns_idx);  // if another slave is present after this one
                  break;
                }
              }
            }
            thisSlaveVials.remove(0,s_idx+1); // start at 0, remove everything before/including this slaveName
            
            // for each vial in list:
            int strLen = thisSlaveVials.length();
            for (int k=0;k<strLen;k++) {  // bug: sometimes iterates an extra time (newline char). prob not super time consuming.
              char thisVialNum = thisSlaveVials.charAt(k);
              int thisVialNum_int = thisVialNum-'0';  // convert from char to int
              // match it to the vial in this slave
              for (int p=0;p<vialsPerSlave;p++) {
                int slave_vialNum = arr_slaves[s].vials[p].vialNum;
                //Serial.print("\tarr_slaves[");  Serial.print(s);  Serial.print("].vials["); Serial.print(p);  Serial.print("].vialNum = "); Serial.print(slave_vialNum);
                // if it matches the slave vial number
                if (slave_vialNum == thisVialNum_int) { 
                  arr_slaves[s].vials[p].mode = paramToSend;
                  Serial.print("\tupdating arr_slaves[");  Serial.print(s);  Serial.print("].vials["); Serial.print(p);  Serial.print("].mode to ");  Serial.println(paramToSend);
                }
              }
            }
          }
        }
      }
    }
  }
  
  // parameter slave needs to update within itself
  else if (firstChar == 'S') {
    // parse out parameter
    String paramToSend = inString;
    int us_idx = paramToSend.indexOf('_');       paramToSend.remove(0,us_idx+1);
    int us_Lidx = paramToSend.lastIndexOf('_');  paramToSend.remove(us_Lidx+1);
        
    int lastUS_idx = inString.lastIndexOf('_');
    String vialList = inString;
    vialList.remove(0,lastUS_idx+1);
    
    for (int s=0;s<numSlaves;s++) {
      char slaveName = arr_slaves[s].slaveName;
      int s_idx = vialList.indexOf(slaveName);

      // if slaveName is in vialList
      if (s_idx!=-1) {
        
        // get vial numbers
        String thisSlaveVials = vialList;
        
        if (s!=numSlaves-1) {
          int ns_idx;
          for (int ns=s+1;ns<numSlaves;ns++) {
            char ns_name = arr_slaves[ns].slaveName;
            ns_idx = thisSlaveVials.indexOf(ns_name);
            if (ns_idx!=-1) {
              thisSlaveVials.remove(ns_idx);  // if another slave is present after this one
              break;
            }
          }
        }
        
        thisSlaveVials.remove(0,s_idx+1); // start at 0, remove everything before/including this slaveName

        // send message to slave
        String toSend = paramToSend + thisSlaveVials;
        
        int cArrSize = toSend.length()+1;
        char charArr[cArrSize];
        toSend.toCharArray(charArr,cArrSize);
        int slaveToSendTo = arr_slaves[s].slaveAddress;

        Wire.beginTransmission(slaveToSendTo);
        Wire.write(charArr);
        Wire.endTransmission();
      }
    
    }
  }
  
  else {
    // unknown string received
    /*
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
    */
  }
}

void requestData(int x) {
  char slaveName = arr_slaves[x].slaveName;
  int slaveAddress = arr_slaves[x].slaveAddress;
  int numVials = arr_slaves[x].numVials;
  int numBytesToReq = 13;
  
  for (int j=0;j<numVials;j++) {
    int thisVialNum = arr_slaves[x].vials[j].vialNum;
    String thisVialMode = arr_slaves[x].vials[j].mode;

    // only request info if the vialmode is set to debug
    if (thisVialMode == "debug") {
      String strSend = "V" + String(thisVialNum);
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
}
