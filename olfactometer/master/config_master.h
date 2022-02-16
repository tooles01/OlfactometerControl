// CONFIG_MASTER

const int baudrate = 9600;    // do not change - needs to match slave code


// constant - these cannot change once uploaded to Arduino
const int numSlaves = 16;                      // number of slaves to check for
const int vialsPerSlave = 8;



// slave address dictionary


char slaveNames[numSlaves] = {'A','B','C','D','E','F'};		    // just for printing - doesn't actually matter


const int slaveAddresses[numSlaves] = {2,3};	// *remove


/*
const int numSlaves = 2;      // *remove : ask the slaves if they there
const int vialsPerSlave[numSlaves] = {2,2};	// *remove
*/

int timeBetweenRequests = 100;			          // can be modified from GUI
