# ST 2020
# run.py

import sys, os
from PyQt5.QtWidgets import (QWidget, QApplication, QHBoxLayout, QComboBox, QPushButton, QLabel, QLineEdit,
                            QVBoxLayout, QFileDialog, QGroupBox)
import utils, config, PIDtesting

class userSelectWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("User Select")
        self.userSelectGroupBox = QGroupBox("Select User:")
        self.userSelectCb = QComboBox()
        self.userSelectCb.addItems(config.users)
        userSelectLayout = QHBoxLayout()
        userSelectLayout.addWidget(self.userSelectCb)
        self.userSelectGroupBox.setLayout(userSelectLayout)
        
        self.createDirectorySelectBox()
        self.doneButton = QPushButton(text="Go",clicked=self.doneSettingUp)
        
        layout = QVBoxLayout()
        layout.addWidget(self.userSelectGroupBox)
        layout.addWidget(self.dirSelectBox)
        layout.addWidget(self.doneButton)
        self.setLayout(layout)
    
    def createDirectorySelectBox(self):
        self.dirSelectBox = QGroupBox()
        defConfigDir = 'C:\\Users\\shann\\Dropbox\\OlfactometerEngineeringGroup\\Control\\software\\github repo'
        defLogDir = 'C:\\Users\\shann\\Dropbox\\OlfactometerEngineeringGroup\\Control\\software\\github repo\\logfiles'
        
        configToolTip = 'Directory that contains config_master.h and config_slave.h'
        configDirLabel = QLabel(text="Config File Directory:",toolTip=configToolTip)
        self.configDirSelectLine = QLineEdit(text=defConfigDir,readOnly=True,toolTip=configToolTip)
        configDirSelectBtn = QPushButton(text="Select",clicked=self.changeConfigDir)
        configLayout = QHBoxLayout()
        configLayout.addWidget(configDirLabel)
        configLayout.addWidget(self.configDirSelectLine)
        configLayout.addWidget(configDirSelectBtn)

        logToolTip = 'Directory that contains all log file folders'
        logDirLabel = QLabel(text="Log File Directory:",toolTip=logToolTip)
        self.logDirSelectLine = QLineEdit(text=defLogDir,readOnly=True,toolTip=logToolTip)
        logDirSelectBtn = QPushButton(text="Select",clicked=self.changeLogDir)
        logDirLayout = QHBoxLayout()
        logDirLayout.addWidget(logDirLabel)
        logDirLayout.addWidget(self.logDirSelectLine)
        logDirLayout.addWidget(logDirSelectBtn)

        hint_label = configDirLabel.sizeHint()
        logDirLabel.setFixedSize(hint_label)
        self.updateLineEditWidth()
        
        layout = QVBoxLayout()
        layout.addLayout(configLayout)
        layout.addLayout(logDirLayout)
        self.dirSelectBox.setLayout(layout)
    
    
    def changeConfigDir(self):
        current_configDir = self.configDirSelectLine.text()
        new_configDir = QFileDialog.getExistingDirectory(self,'Select Folder',current_configDir)
        #new_configDir = QFileDialog.getExistingDirectory(self,'Select Folder',current_configDir,QFileDialog.DontUseNativeDialog)
        ### ^^^ this option lets you see the files also, but it's super ugly and hard to move around in
        self.configDirSelectLine.setText(new_configDir)
        self.updateLineEditWidth()

    def changeLogDir(self):
        current_logDir = self.logDirSelectLine.text()
        new_logDir = QFileDialog.getExistingDirectory(self,'Select Folder',current_logDir)
        self.logDirSelectLine.setText(new_logDir)
        self.updateLineEditWidth()
    
    def updateLineEditWidth(self):
        fm_c = self.configDirSelectLine.fontMetrics()
        w_c = fm_c.boundingRect(self.configDirSelectLine.text()).width()
        fm_l = self.logDirSelectLine.fontMetrics()
        w_l = fm_l.boundingRect(self.logDirSelectLine.text()).width()
        if w_c > w_l: w = w_c
        else: w = w_l
        self.configDirSelectLine.setMinimumWidth(w+15)
        self.logDirSelectLine.setMinimumWidth(w+15)
    
    def doneSettingUp(self):
        selected_user = self.userSelectCb.currentText()
        selected_configDir = self.configDirSelectLine.text()
        selected_logDir = self.logDirSelectLine.text()
        
        if not selected_logDir:
            print("pls select a log directory")
        else:
            if not selected_configDir:
                print("pls select a config directory")
            else:
                # if it doesn't already exist, create today's folder & move into it; create logger
                os.chdir(selected_logDir)
                today_logDir = selected_logDir + '\\' + config.currentDate
                if not os.path.exists(today_logDir):
                    os.mkdir(today_logDir)
                os.chdir(today_logDir)
                logger = utils.createCustomLogger(__name__)
                
                # check that config dir contains files you need
                os.chdir(selected_configDir)
                files = os.listdir()
                if (not 'config_master.h' in files) or (not 'config_slave.h' in files):    
                    if not 'config_master.h' in files:  logger.error('selected config directory does not contain config_master.h - select a different directory')
                    if not 'config_slave.h' in files:   logger.error('selected config directory does not contain config_slave.h - select a different directory')
                else:
                    logger.info('User: %s', selected_user)
                    logger.info('~~~Finished setup~~~')

                    # get default slave information
                    os.chdir(selected_configDir)
                    ardConfig = utils.getArduinoConfigFile('config_master.h')
                    defNumSlaves = int(ardConfig.get('numSlaves'))
                    defSlaveNames = ardConfig.get('slaveNames[numSlaves]')
                    defvPSlave = ardConfig.get('vialsPerSlave[numSlaves]')
                    
                    # call GUIMain
                    logger.debug('Creating instance of GUIMain')
                    self.mainWindow = PIDtesting.GUIMain(selected_configDir,today_logDir,defNumSlaves,defSlaveNames,defvPSlave)
                    self.mainWindow.show()
                    logger.debug('Closing self')
                    self.close()
        

if __name__ == "__main__":
    app1 = QApplication(sys.argv)
    w1 = userSelectWindow()
    w1.show()
    sys.exit(app1.exec_())