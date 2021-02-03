// CONFIG_MASTER

const int baudrate = 9600;

const int numSlaves = 4;
char slaveNames[numSlaves] = {'A','B','C','D'};
const int slaveAddresses[numSlaves] = {2,3,4,5};
const int vialsPerSlave[numSlaves] = {2,2,2,2};

int timeBetweenRequests = 100;