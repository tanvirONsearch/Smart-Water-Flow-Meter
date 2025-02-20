from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
from pymodbus.client import ModbusSerialClient as mb
import time
import numpy as np

class CalibrationWindow(QtWidgets.QDialog):
    calib_data = pyqtSignal(object) #emitting calibration value for main window

    def __init__(self,client,active):
        super().__init__()
        self.setWindowTitle("Calibration window")
        self.setFixedSize(800, 600)
        self.slave_id = 1
        self.active =np.zeros(10,dtype=bool)
        self.curV = np.zeros(10,dtype=np.uint32)

        self.active = active

        self.startValue = 0
        self.recordValue = 0
        self.flag = 0

        self.pulsePerLitre = 1
        self.calib_reg = np.ones(10,dtype= np.int16)

        self.client = client
        #self.client = mb(port='COM8', baudrate=115200, stopbits=2, timeout=.1)
        if not self.client.connect():
            QtWidgets.QMessageBox.critical(self, "Connection Error", "Failed to Establish connection.")
            time.sleep(10)
            exit()

     # Layout for the dialog
        layout = QtWidgets.QVBoxLayout(self)

     # Dropdown (ComboBox)
        self.dropdownMenu = QtWidgets.QHBoxLayout()
        self.dropdown = QtWidgets.QComboBox(self)
        self.dropdown.addItems(["Meter 1", "Meter 2", "Meter 3", "Meter 4", 
                                "Meter 5","Meter 6","Meter 7","Meter 8",
                                "Meter 9","Meter 10"])
        
        self.dropdownMenu.addWidget(self.create_label("Select Meter:", font_size=20))
        self.dropdownMenu.addWidget(self.dropdown)
        layout.addLayout(self.dropdownMenu)

        self.dropdown.currentIndexChanged.connect(self.update_slave_id)

     # calibration target from refrence meter 
        self.inputMenu = QtWidgets.QHBoxLayout()

        self.number_input = QtWidgets.QSpinBox()  # For integer input
        self.number_input.setMinimum(1)  # Set minimum value
        self.number_input.setMaximum(100)  # Set maximum value
        self.number_input.setValue(1)  # Default value
        self.inputMenu.addWidget(self.create_label("Set Refrence target value(Litre):", font_size=20))
        self.inputMenu.addWidget(self.number_input)

        layout.addLayout(self.inputMenu)
        


     # displaying values of meters:
        self.lcdNumber = QtWidgets.QLCDNumber(self)
        self.lcdNumber.setDigitCount(8)
        self.lcdNumber.setProperty("intValue", 0)    
        self.lcdNumber.setObjectName("lcdNumber")
        self.lcdNumber.setStyleSheet("""
        background-color: rgba(255,255,255,1);
        border: 3px solid rgba(0,0,0,1);
        font-weight: bold;
        font-size: 18px;
        color: rgba(10,10,15,1);
        """)

        self.pulseLabel = self.create_label("Current pulse count :", font_size=20)
        layout.addWidget(self.pulseLabel)
        layout.addWidget(self.lcdNumber)
        

     # Button
        self.calibrate_button1 = QtWidgets.QPushButton("start", self)
        self.calibrate_button2 = QtWidgets.QPushButton("Record", self)
        self.calib_button_layout = QtWidgets.QHBoxLayout()
        self.calib_button_layout.addWidget(self.calibrate_button1)
        self.calib_button_layout.addWidget(self.calibrate_button2)

        self.calibrate_button1.clicked.connect(self.start) # start button
        self.calibrate_button2.clicked.connect(self.record) # start button


        layout.addLayout(self.calib_button_layout)
        self.instLabel = self.create_label("press start to start calibrating pulse Count to litre", font_size=20)
        layout.addWidget(self.instLabel)

        self.setLayout(layout)

        self.active_slave()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.data)
        # self.timer.start(50)  # Update every 100 ms (.1 second)


    def active_slave(self):
        # for id in range(10):
        #     response = self.client.read_holding_registers(address=0, count=1, slave=id+1)
        #     if not response.isError():
        #         self.active[id]=True

        for i,state in enumerate(self.active):
            if not state:
                self.dropdown.setItemData(i, QtGui.QColor('red'), QtCore.Qt.ForegroundRole)
                self.dropdown.model().item(i).setEnabled(False)
            else:
                self.dropdown.setItemData(i, QtGui.QColor('Green'), QtCore.Qt.ForegroundRole)
                self.dropdown.model().item(i).setEnabled(True)

    def create_label(self, text, font_size=12, color="black"):
        label = QtWidgets.QLabel(text)
        label.setStyleSheet(f"font-size: {font_size}px; color: {color};")
        return label

    def update_slave_id(self,idx):
        self.slave_id = idx + 1
        self.instLabel.setText("press 'start' to start calibrating pulse Count to litre",)
        self.instLabel.setStyleSheet("color: black; font-size: 20px;")

    def start(self):
        self.timer.start(50)  # Update every 100 ms (.1 second)
        """Perform calibration logic."""
        self.calibrate_button1.setEnabled(False)
        self.timer.start(50)
        self.instLabel.setText(
            f"Started! Press 'Record' when the reference meter\nchanges by: {self.number_input.value()} litre."
        )
        self.instLabel.setStyleSheet("color: darkblue; font-size: 20px;")
        self.flag = 1
        self.dropdown.setDisabled(True)
        self.calibrate_button2.setEnabled(True)

    def record(self):
        self.calibrate_button2.setEnabled(False)
        self.timer.stop()
        self.pulsePerLitre = self.recordValue - self.startValue

        self.calib_reg[self.slave_id-1] = self.pulsePerLitre if self.pulsePerLitre>0 else 1

        self.calib_data.emit(self.calib_reg)

        self.instLabel.setText(f"Recorded! \n{self.pulsePerLitre} pulses per litre.")
        self.instLabel.setStyleSheet("color: green; font-size: 20px;")
        self.dropdown.setDisabled(False)

        self.calibrate_button1.setEnabled(True)


    def data(self):
        #print('inside this function fuck')
        try:
            response = self.client.read_holding_registers(address=0, count=4, slave=self.slave_id)
            if not response.isError():
                ##pulse count from arduino::pulseCount-prevPulseCount
                register_2 = response.registers[2]
                register_3 = response.registers[3]

                self.curV[self.slave_id-1] = (register_2 * 65536 + register_3)

                # Update the LCD displays
                if self.flag == 1:
                    self.startValue = self.curV[self.slave_id-1]
                    self.flag = 2
                elif self.flag == 2:
                    self.recordValue = self.curV[self.slave_id-1]
                    self.lcdNumber.display(self.curV[self.slave_id-1]-self.startValue)
            else:
                pass        
        except Exception as e:
            exit()

    def closeEvent(self, event):
        """Handle application close event."""
        self.client.close()
        super().closeEvent(event)


