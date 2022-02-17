/*
  master.ino
  
  Version:  0.2.1
  Author:   S.Toole
  
  Notes:    Update to communication strings. New string format allows multiple slave/vial updates with a single command.
            First character: 'M' indicates master settings update. 'S' indicates data to send to slave
*/

#include <Wire.h>
#include "config_master.h"

String masterMode = "debug";


// vialInfo
typedef struct {
  int vialNum;
  String mode = "debug";
} vialInfo;

// slaveInfo
typedef struct {
  int slaveActive;
  int slaveAddress;
  char slaveName;
  vialInfo vials[vialsPerSlave];    // set this just for creating all the structs
  
  String mode = "normal"; // get rid of this
  int prevRequestTime;
} slaveInfo;

slaveInfo arr_slaveInfos[numSlaves];  // array of slaveInfo objects


// slave address dictionary
typedef struct {
  char slaveName;
  int address;
} dictEntry;

dictEntry arr_addresses[numSlaves];


void setup() {
  
  Serial.begin(baudrate);
  Serial.setTimeout(30);   // max # of ms to wait for serial data in readString
                           // -> this is how quickly we can send multiple commands in a row from python GUI without it combining them all
  
  Wire.begin();
  Wire.setTimeout(250);  // unclear that this works
  
  
  // SLAVE NAME & ADDRESS DICTIONARY   --> ** move this somewhere else, config or something
  arr_addresses[0].slaveName = 'A'; arr_addresses[0].address = 3;
  arr_addresses[1].slaveName = 'B'; arr_addresses[1].address = 4;
  arr_addresses[2].slaveName = 'C'; arr_addresses[2].address = 1;
  arr_addresses[3].slaveName = 'D'; arr_addresses[3].address = 2;
  arr_addresses[4].slaveName = 'E'; arr_addresses[4].address = 0;
  arr_addresses[5].slaveName = 'F'; arr_addresses[5].address = 5;
  
  
  // POPULATE SLAVE ARRAY (arr_slaveInfos)
  for (int i=0;i<numSlaves;i++) {
    
    // vial numbers
    for (int j=0;j<vialsPerSlave;j++) {
      arr_slaveInfos[i].vials[j].vialNum = j+1;
    }

    // get slave address (request from slave)
    int address = sayHey(i);
    
    // slave active or not; if active: get slave name (from dictionary)
    char slaveName = '-';
    if (address == 99) {
      arr_slaveInfos[i].slaveActive = 0;  // slave not active
    }
    else {
      arr_slaveInfos[i].slaveActive = 1;  // slave is active
      // get slave name (from dictionary)
      for (int k=0;k<numSlaves;k++) {
        if (arr_addresses[k].address == address) {
          slaveName = arr_addresses[k].slaveName;
        }
      }
    }
    arr_slaveInfos[i].slaveAddress = address;
    arr_slaveInfos[i].slaveName = slaveName;
  }

  printSlaveInfo();
}

void loop() {
  if (Serial.available()) {
    String inString = Serial.readString();
    parseSerial(inString);
  }
  
  else {
    for (int x=0;x<numSlaves;x++) {
      unsigned long currentTime = millis();
      int prevRequestTime = arr_slaveInfos[x].prevRequestTime;
      int timeSinceLast = currentTime-prevRequestTime;
      
      if (timeSinceLast >= timeBetweenRequests) {
        arr_slaveInfos[x].prevRequestTime = currentTime;
        requestData(x);
      }
    }
  }
  
}


void parseSerial(String inString) {
  char firstChar = inString[0];

  // something to update within the master
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
        if (masterMode == "debug") {
          Serial.print("updating time between requests to ");
          Serial.print(timeBetweenRequests);
          Serial.print(" ms\n");
        }
      }
    }
    
    // update .. ?
    else if (secChar == 'S') {
      
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
        char slaveName = arr_slaveInfos[s].slaveName;
        int s_idx = vialList.indexOf(slaveName);
        
        // if slaveName is in vialList
        if (s_idx!=-1) {
          // get vial numbers
          String thisSlaveVials = vialList;
          
          // if it's not the last slave
          if (s!=numSlaves-1) {
            // for each slave that exists after this one: remove data
            int ns_idx;
            for (int ns=s+1;ns<numSlaves;ns++) {
              char ns_name = arr_slaveInfos[ns].slaveName;
              ns_idx = thisSlaveVials.indexOf(ns_name);
              if (ns_idx!=-1) {
                thisSlaveVials.remove(ns_idx);  // if another slave is present after this one
                break;
              }
            }
          }
          // get the vial numbers for just this slave
          thisSlaveVials.remove(0,s_idx+1); // start at 0, remove everything before/including this slaveName
          
          // for each vial in this slave's list:
          int strLen = thisSlaveVials.length();
          for (int k=0;k<strLen;k++) {  // bug: sometimes iterates an extra time (newline char). prob not super time consuming.
            
            // get vial number
            char thisVialNum = thisSlaveVials.charAt(k);
            int thisVialNum_int = thisVialNum-'0';  // convert from char to int
            
            // match it to the vial in this slave
            for (int p=0;p<vialsPerSlave;p++) { // edit: this may be excessive
              int slave_vialNum = arr_slaveInfos[s].vials[p].vialNum;
              
              // if it matches the slave vial number: update this vial's mode
              if (slave_vialNum == thisVialNum_int) {
                arr_slaveInfos[s].vials[p].mode = paramToSend;
                if (masterMode == "debug") {
                  Serial.print("\tupdating arr_slaveInfos[");
                  Serial.print(s);
                  Serial.print("].vials[");
                  Serial.print(p);
                  Serial.print("].mode to ");
                  Serial.println(paramToSend);
                }
              }
            }
          }
        }
      }
    }

    else {
      Serial.println("unknown string received");
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

    // send to slaves in list
    for (int s=0;s<numSlaves;s++) {
      char slaveName = arr_slaveInfos[s].slaveName;
      int s_idx = vialList.indexOf(slaveName);

      // if slaveName is in vialList
      if (s_idx!=-1) {
        
        // get vial numbers
        String thisSlaveVials = vialList;
        
        if (s!=numSlaves-1) {
          int ns_idx;
          for (int ns=s+1;ns<numSlaves;ns++) {
            char ns_name = arr_slaveInfos[ns].slaveName;
            ns_idx = thisSlaveVials.indexOf(ns_name);
            if (ns_idx!=-1) {
              thisSlaveVials.remove(ns_idx);  // if another slave is present after this one
              /*
              if (masterMode == "debug") {
                Serial.print("thisSlaveVials = ");
                Serial.print(thisSlaveVials);
                Serial.println();
              }
              */
              break;
            }
          }
        }
        
        thisSlaveVials.remove(0,s_idx+1); // start at 0, remove everything before/including this slaveName
        /*
        if (masterMode == "debug") {
          Serial.print("thisSlaveVials = ");
          Serial.print(thisSlaveVials);
          Serial.println();
        }  
        */
        /*
        Serial.print("slave: "); Serial.print(arr_slaveInfos[s].slaveName);
        Serial.print("\tvials: "); Serial.print(thisSlaveVials);
        Serial.print("\tlength of vial string: ");  Serial.print(thisSlaveVials.length());
        Serial.println();
        for (int v=0;v<=thisSlaveVials.length();v++) {
          Serial.print("thisSlaveVials[");  Serial.print(v);  Serial.print("]:");
          char toPrint = thisSlaveVials[v];
          Serial.println(toPrint);
        }
        */
        
        // send message to slave
        String toSend = paramToSend + thisSlaveVials;
        
        int cArrSize = toSend.length()+1;
        char charArr[cArrSize];
        toSend.toCharArray(charArr,cArrSize);
        int slaveToSendTo = arr_slaveInfos[s].slaveAddress;
        
        Serial.print("sending: ");
        Serial.print(charArr);
        Serial.print("\tto slave at address ");
        Serial.println(slaveToSendTo);
        
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
      if (firstChar == arr_slaveInfos[p].slaveName) {
        slaveToSendTo = arr_slaveInfos[p].slaveAddress;
      }
    }
    Wire.beginTransmission(slaveToSendTo);
    Wire.write(charArr);
    Wire.endTransmission();
    */
  }
}


void requestData(int x) {
  char slaveName = arr_slaveInfos[x].slaveName;
  int slaveAddress = arr_slaveInfos[x].slaveAddress;
  int numBytesToReq = 13;
  
  for (int j=0;j<vialsPerSlave;j++) {
    int thisVialNum = arr_slaveInfos[x].vials[j].vialNum;
    String thisVialMode = arr_slaveInfos[x].vials[j].mode;

    // only request info if the vialmode is set to debug
    if (thisVialMode == "debug") {
      String strSend = "V" + String(thisVialNum);
      int numChars = strSend.length() + 1;
      char strSend_[numChars];
      strSend.toCharArray(strSend_,numChars);
      if (masterMode == "debug") {
        Serial.print("\nsent:\t\t");
        Serial.print(strSend);
        Serial.print("\t\tto address ");
        Serial.print(slaveAddress);
        Serial.print(" (slave ");
        Serial.print(arr_slaveInfos[x].slaveName);
        Serial.print(")");
        Serial.println();
      }
      
      Wire.beginTransmission(slaveAddress);
      Wire.write(strSend_);
      Wire.endTransmission();
      
      Wire.requestFrom(slaveAddress,numBytesToReq,true);
      
      if (masterMode == "debug") {
        Serial.print("received:\t");
      }
      else {
        Serial.print(slaveName);
      }
            
      for (int a=0;a<numBytesToReq;a++) {
        char fromSlave = Wire.read();
        Serial.print(fromSlave);
      }
      Serial.println();
      
      /*
      if (masterMode == "debug") {
        Serial.print("string '");
        Serial.print(whatDoWeGet);
        Serial.print("' (length: ");
        Serial.print(whatDoWeGet.length());
        Serial.print(" chars, size: ");
        Serial.print(sizeof(whatDoWeGet));
        Serial.print(" bytes)");
        Serial.println();
        Serial.println("end of transmission from slave");
      }
      */
    }
  }
}



int sayHey(int addressToCheck) {
  int recAddr = 0;
  
  // tell slave what we're doing
  Wire.beginTransmission(addressToCheck);
  Wire.write("hey");
  Wire.endTransmission();
  
  
  // request address from slave
  Wire.requestFrom(addressToCheck,2,true);  // *** ADD A TIMEOUT INTO THIS
  
  if (Wire.available()) {
    String receivedStr = "";
    while (Wire.available()) {
      char inChar = Wire.read();
      receivedStr += inChar;
    }
    recAddr = receivedStr[0];
    recAddr = recAddr-'0';    // convert from char to int
  }
  else {
    recAddr = 99; // if nothing is received back from the slave
  }
  
  return recAddr;
}




void printSlaveInfo() {
  // print list of slaves n shit for funsies
  Serial.println("~~~~~~~~~~~~~~~~~~");
  for (int i=0; i<numSlaves;i++) {
    Serial.print(arr_slaveInfos[i].slaveName);
    Serial.print("\tslaveAddress: "); Serial.print(arr_slaveInfos[i].slaveAddress);
    //Serial.print("\tslaveActive: ");  Serial.print(arr_slaveInfos[i].slaveActive);
    Serial.println();
  }
  Serial.println();
}
