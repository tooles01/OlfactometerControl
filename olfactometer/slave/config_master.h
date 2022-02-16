// CONFIG_MASTER

const int baudrate = 9600;			// do not change

// constant - these cannot change once uploaded to Arduino
const int numSlaves = 2;			// *remove : ask the slaves if they there
char slaveNames[numSlaves] = {'A','B'};		// just for printing - doesn't actually matter
const int slaveAddresses[numSlaves] = {2,3};	// *remove
const int vialsPerSlave[numSlaves] = {2,2};	// *remove

int timeBetweenRequests = 100;			// can be modified from GUI


