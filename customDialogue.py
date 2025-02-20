from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication, QLineEdit
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QIntValidator, QFont
import sys
import numpy as np

class CInputDialog(QDialog):
    def __init__(self, parent=None):
        super(CInputDialog, self).__init__(parent)
        self.setWindowTitle("Smart Flow Meter")
        self.setWindowIcon(QIcon('resources/flowLogo.png'))

        self.VLayout = QVBoxLayout(self)
        self.label = QLabel("Enter New Value:")
        self.label.setFont(QFont("Helvetica", 12))
        self.label.setAlignment(Qt.AlignTop)
        self.VLayout.addWidget(self.label)

        # Input field with integer validator
        self.input = QLineEdit(self)
        self.input.setFixedHeight(50)
        self.input.setFont(QFont("Helvetica", 16))
        self.input.setValidator(QIntValidator())  # Only allow integer input
        self.VLayout.addWidget(self.input)

        # Buttons for "OK" and "Cancel"
        self.buttonLayout = QHBoxLayout()
        self.ok_button = QPushButton("   OK   ")
        self.ok_button.setStyleSheet("""
        QPushButton {
        background-color: #3498db;
        color: white;
        border: 2px solid #2980b9;
        border-radius: 10px;
        font-size: 18px;
        padding: 8px;
        }
        QPushButton:hover {
        background-color: #2980b9;
        }
        QPushButton:pressed {
        background-color: #1c6693;
        }
        """)

        self.cancel_button = QPushButton(" Cancel ")
        self.cancel_button.setStyleSheet("""
        QPushButton {
        background-color: #3498db;
        color: white;
        border: 2px solid #2980b9;
        border-radius: 10px;
        font-size: 18px;
        padding: 8px;
        }
        QPushButton:hover {
        background-color: #2980b9;
        }
        QPushButton:pressed {
        background-color: #1c6693;
        }
        """)
        self.buttonLayout.addWidget(self.ok_button)
        self.buttonLayout.addWidget(self.cancel_button)
        self.VLayout.addLayout(self.buttonLayout)

        # Timer for detecting hold
        self.hold_timer = QTimer()
        self.hold_timer.setInterval(700)  # 700 ms hold interval
        self.hold_timer.setSingleShot(True)
        self.hold_timer.timeout.connect(self.on_hold_complete)

        self.hold_confirmed = 1

        self.ok_button.pressed.connect(self.start_timer)
        self.ok_button.released.connect(self.stop_timer)
        self.cancel_button.pressed.connect(self.reject)

    def start_timer(self):
        self.hold_timer.start()

    def stop_timer(self):
        if self.hold_timer.isActive():
            self.hold_timer.stop()
            self.hold_confirmed = 1 
        self.accept()

    def on_hold_complete(self):
        self.hold_confirmed = 2 
        self.accept()

    def getInteger(self):
        if self.exec_() == QDialog.Accepted:
            # Check if the input is valid and return the integer and hold status
            if self.input.text().isdigit() and self.input.text() is not None:  # Ensures input is a valid integer
                value = int(self.input.text())
                if value >= 0 and value <= 2**32 - 1:  # Check if within the 32-bit unsigned range
                    x = (np.uint32(value), self.hold_confirmed)
                else:
                    x = (np.uint32(2**32 - 1), self.hold_confirmed)  # Cap at the max 32-bit unsigned value
                return x
        return None, 0


    # def getInteger(self):
    #     if self.exec_() == QDialog.Accepted:
    #         # Check if the input is valid and return the integer and hold status
    #         if self.input.text().isdigit() and self.input.text() is not None:  # Ensures input is a valid integer
    #             if int(self.input.text()) <= 2**32 -1:
    #                 x =  (np.uint32(self.input.text()), self.hold_confirmed)
    #             else: x = (np.uint32(2**32 -1 ), self.hold_confirmed)
    #             return x
    #     return None, 0

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = CInputDialog()
    value, hold_status = dialog.getInteger()
    if value is not None:
        print(f"Value: {value}, Hold Status: {hold_status}")
    else:
        print("Operation Cancelled")
