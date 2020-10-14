// CONFIG_SLAVE.H

const int timeToWait = 2;		// time to wait before running PID on same line
const int maxValveOpenTime = 5000;	// max time for isolation valve to be open (ms)

float defKp = 0.050;
float defKi = 0.0001;
float defKd = 0.000;

int sensPins[2] = {A0, A1};
int ctrlPins[2] = {4, 5};
int valvPins[2] = {22, 23};

typedef struct {
  // pin numbers
  int vialNum;
  int sensPin;
  int ctrlPin;
  int valvPin;

  int valveState = 0;
  String setting = "testing";

  // PID variables
  bool PIDon = false;
  int setpoint = 100;
  float Kp = defKp;
  float Ki = defKi;
  float Kd = defKd;

  int flowVal;
  unsigned long prevTime;
  int prevError;
  int prevOutput;
  int output;
  int integral;

  // receive from master
  unsigned long timeReceived;
  unsigned long timeToClose = 0;
} vialInfo;

