# *** this is outdated  - updated repository at OlfaControl_Arduino
#


- make environment in this folder (C:\Users\SB13FLLT004\Dropbox (NYU Langone Health)\OlfactometerEngineeringGroup (2)\Control\a_software\OlfactometerControl)
- activate environment
- run "pip install -r requirements.txt"


# OlfactometerControl
source files and documentation for control of 50-odor olfactometer prototype


1. Upload slave_A.ino to Arduino Slave A & slave_B.ino to Arduino Slave B
2. Upload master.ino to Arduino master
3. Run run.py




notes:
- master & slave codes include config files at locations hard coded to my PC - needs to be edited by user
- slave A and slave B codes are identical except for line 8: slaveIndex



# REQUIREMENTS FILE
- removed pandas, pyqtgraph, nidaqmx
