# ST 2020
# run.py

import sys
from PyQt5.QtWidgets import QApplication
import utils, channel_stuff, mainGUI


if __name__ == "__main__":
    # Create logger
    mainLogger = utils.createLogger(__name__)
    logFileLoc = mainLogger.handlers[0].baseFilename
    mainLogger.info('Logging to %s', logFileLoc)
    
    app1 = QApplication(sys.argv)
    
    # Default Channel objects
    channelObjs = []
    channelObjs.append(channel_stuff.channelObj(name='olfa prototype',instrument='olfactometer'))
    channelObjs.append(channel_stuff.channelObj(name='PID reading',instrument='NI-DAQ'))
    
    # Open main window
    mainWindow = mainGUI.mainGUI(channelObjs)
    mainWindow.show()

    sys.exit(app1.exec_())