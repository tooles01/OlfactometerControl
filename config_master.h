// CONFIG_MASTER

const int baudrate = 9600;

const int numSlaves = 2;
const int vialsPerSlave[numSlaves] = {2, 1};
char slaveNames[numSlaves] = {'A','B'};

const int slaveAddresses[numSlaves] = {2, 3};

int timeBetweenRequests = 100;