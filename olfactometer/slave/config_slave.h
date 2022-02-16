// CONFIG_SLAVE.H

// dipswitch pins to read slave address from
#define dipSwitch1  A11
#define dipSwitch2  A10
#define dipSwitch3  A9
#define dipSwitch4  A8

const int baudrate = 9600;
const int numVials = 8;

const int timeToWait = 2;		        // time to wait before running PID on same line
const int maxValveOpenTime = 5000;	// max time for isolation valve to be open (ms)

float defKp = 0.050;
float defKi = 0.0001;
float defKd = 0.000;
int defSp = 100;

int sensPins[numVials] = {A0, A1, A2, A3, A4, A5, A6, A7};
int ctrlPins[numVials] = {4, 5, 6, 7, 8, 9, 10, 11};
int valvPins[numVials] = {22, 23, 24, 25, 26, 27, 28, 29};

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
  int setpoint = defSp;
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
