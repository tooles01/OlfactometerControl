# ST 2020
# slave.py

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout
from instrumentDrivers import vial


class Slave(QGroupBox):

    def __init__(self, parent, slaveName, numVials, sensorTypes):
        super().__init__()
        self.slaveName = slaveName
        self.numVials = numVials
        self.sensorTypes = sensorTypes

        # error if len(sensorTypes) is less than numVials

        layout = QVBoxLayout()
        self.vials = []
        for x in range(numVials):
            v_vialNum = x+1
            try:
                v_sensorType = sensorTypes[v_vialNum]
            except IndexError:
                v_sensorType = sensorTypes[0]
                print("no sensor type listed for slave " + self.slaveName + " vial " + str(vialNum) + ": using default sensor type")
            v_vial = vial.Vial(parent,slaveName,v_vialNum,v_sensorType)
            self.vials.append(v_vial)
            layout.addWidget(v_vial)
        
        self.setTitle("Slave " + self.slaveName)
        self.setLayout(layout)