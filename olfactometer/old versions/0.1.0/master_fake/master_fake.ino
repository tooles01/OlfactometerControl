// ST 2020
// master_fake.ino

// fake master for testing with Python GUI

//#include <C:\Users\shann\Dropbox (NYU Langone Health)\OlfactometerEngineeringGroup (2)\Control\software\OlfactometerControl\olfactometer\config_master.h>
#include <C:\Users\shann\Dropbox (NYU Langone Health)\OlfactometerEngineeringGroup (2)\Control\a_software\OlfactometerControl\olfactometer\config_master.h>
int ledpin = 13;

typedef struct {
  char slaveName;
  int slaveAddress;
  int numVials;
  int lastFlow = 0;
  int lastCtrl = 0;
  
  String mode = "normal";
  int prevRequestTime;
} slaveInfo;
slaveInfo arr_slaves[numSlaves];


void setup() {
  pinMode(ledpin, OUTPUT);
  digitalWrite(ledpin, HIGH);
  int timeBetweenRequests = 500;
  Serial.begin(baudrate);
  for (int i=0;i<numSlaves;i++) {
    arr_slaves[i].slaveName = slaveNames[i];
    arr_slaves[i].numVials = vialsPerSlave[i];
    arr_slaves[i].slaveAddress = slaveAddresses[i];
  }
  digitalWrite(ledpin, LOW);
}

void loop() {
  if (Serial.available()) {
    String inString = Serial.readString();
    parseSerial(inString);
  }

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
  }
  else {
    int state = digitalRead(ledpin);
    if (state == HIGH) {
      digitalWrite(ledpin, LOW);
    }
    else {
      digitalWrite(ledpin, HIGH);
    }
  }
}

void requestData(int x) {
  char slaveName = arr_slaves[x].slaveName;
  int numVials = arr_slaves[x].numVials;
  
  for (int vialNum=1;vialNum<=numVials;vialNum++) {
    int newFlow = arr_slaves[x].lastFlow + 3;
    int newCtrl = arr_slaves[x].lastCtrl + 3;
    if (newFlow > 1024) { newFlow = 0; }
    if (newCtrl > 255) { newCtrl = 0; }
    
    String flowVal = zeroPadInteger(newFlow);
    String ctrlVal = zeroPadInteger(newCtrl);
    arr_slaves[x].lastFlow = newFlow;
    arr_slaves[x].lastCtrl = newCtrl;
    String blankVals = "0000";
    Serial.print(slaveName);
    Serial.print(vialNum);
    Serial.print(flowVal);
    Serial.print(ctrlVal);
    Serial.print(blankVals);
    Serial.println();
  }  
}



String zeroPadInteger (int value) {
  String valString;
  
  if (value < 10) {valString = "000";}
  else if (value < 100) {valString = "00";}
  else if (value < 1000) {valString = "0";}
  valString += String(value);
  
  return valString;
}
