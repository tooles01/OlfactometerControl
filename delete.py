import sys
from PyQt5.QtWidgets import QDialog, QPushButton, QVBoxLayout, QApplication
from PyQt5 import QtCore, QtGui




import logging, os
import utils

dir1 = os.getcwd()
logger1 = utils.createCustomLogger(__name__)
x1 = logger1.handlers[0].baseFilename

defLogDir = 'C:\\Users\\shann\\Dropbox\\OlfactometerEngineeringGroup\\Control\\software\\github repo\\logfiles'
os.chdir(defLogDir)
dir2 = os.getcwd()
logger2 = utils.createCustomLogger(__name__)
x2 = logger2.handlers[0].baseFilename

# no matter what, it makes it 



class Dialog(QDialog):
    def __init__(self, val):
        super().__init__()
        self.val = val
        self.initUI()

    def initUI(self):
        endButton = QPushButton('OK')
        endButton.clicked.connect(self.on_clicked)
        lay = QVBoxLayout(self)
        lay.addWidget(endButton)
        self.setWindowTitle(str(self.val))

    @QtCore.pyqtSlot()
    def on_clicked(self):
        self.val += 1
        self.accept()

def main(): 
    app = QApplication(sys.argv)    # create application
    for i in range(10):
        ex = Dialog(i)              # open dialog and get ? 
        ex.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        if ex.exec_() == QDialog.Accepted:
            print(ex.val)

if __name__ == '__main__':
    main()