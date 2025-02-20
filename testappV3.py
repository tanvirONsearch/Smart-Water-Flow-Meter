from pymodbus.client import ModbusSerialClient as mb
from PyQt5 import QtCore,QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication, QInputDialog, QLineEdit, QMessageBox, QStyledItemDelegate
from PyQt5.QtGui import QPixmap,QColor, QIcon
from PyQt5.QtCore import Qt
import serial.tools
import serial.tools.list_ports
from QRoundProgressbar import RoundProgressbar
from customDialogue import CInputDialog
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox
import pyqtgraph as pg
from DataManager import DataManager
from calib import CalibrationWindow

import sys
import time
from datetime import datetime
from datetime import time as tyme
import os
import pandas as pd
from threading import Lock
import serial
import numpy as np


'''
maximum input 99999999. line 1274 fix it to accumulate lakh litre.
In worker thread fix Ctotal dtype to float64, div by 1lakh , store upto 2 decimal point
in filegen.py fix accordingly
fix reset logic
fix second page . handle saving data. of the second page.
'''
'''
fixed 
--------------------------
lakh litre problem

'''

'''Splash screen'''
class SplashScreen(QtWidgets.QSplashScreen):
    def __init__(self, image_path, parent=None):
        super(SplashScreen, self).__init__(parent)

        # Loading and setting the background image
        pixmap = QtGui.QPixmap(image_path)
        self.setPixmap(pixmap)

        # Setting text font and alignment
        self.status_text = ""
        self.text_color = QtGui.QColor("white")
        self.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))

    def show_status(self, text):
        self.status_text = text
        self.update()  # Repaint the splash screen with the new status text

    def drawContents(self, painter):
        painter.setPen(self.text_color)
        painter.drawText(self.rect(), QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter, self.status_text)

"""Spacer class """
class SpacedItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(SpacedItemDelegate, self).__init__(parent)

    def sizeHint(self, option, index):
        size = super(SpacedItemDelegate, self).sizeHint(option, index)
        size.setHeight(size.height() + 18)  
        return size

"""UI setup class """
class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 480)
        MainWindow.setMinimumSize(QtCore.QSize(50, 30))
        MainWindow.setStyleSheet("background-color: rgb(255, 255, 255);")

        self.central_stack_widget = QtWidgets.QStackedWidget(MainWindow)
        self.central_stack_widget.setObjectName('main weidget')

        '''Page 2'''
        self.second_page = QtWidgets.QWidget()
        self.second_page.setObjectName("second_page")

        # Second Page Layout
        self.second_page_layout = QtWidgets.QVBoxLayout(self.second_page)
        self.second_page_layout.setContentsMargins(0, 0, 0, 0)
        self.second_page_layout.setSpacing(10)

        # Labels
        self.labels = [
            [QtWidgets.QLabel(f"Label {row}{col}") for col in range(2)]
            for row in range(10)
        ]
        #LCD
        self.lcd_displays = [
            [QtWidgets.QLCDNumber() for col in range(2)]
            for row in range(10)
        ]
        _ = [j.setDigitCount(12) for i in self.lcd_displays for j in i ]

        # Create and populate horizontal layouts for each row
        self.hlayouts = []
        for row in range(10):  # Iterate through rows
            hlayout = QtWidgets.QHBoxLayout()
            for col in range(2):  # Add label and LCD for each column
                    hlayout.addWidget(self.labels[row][col])      # Add label
                    hlayout.addWidget(self.lcd_displays[row][col])  # Add LCD display
            self.hlayouts.append(hlayout)  # Save the horizontal layout
            self.second_page_layout.addLayout(hlayout)

        #styling labels
        for i in range(10):
            for j in range(2):
                if j%2==0:
                    self.styleLabel(self.labels[i][j],1,i)
                else:
                    self.styleLabel(self.labels[i][j],0,i)
        
        self.central_stack_widget.addWidget(self.second_page)

        
        '''page 1'''
        self.first_page = QtWidgets.QWidget()
        self.first_page.setObjectName("first_page")
        self.gridLayout = QtWidgets.QGridLayout(self.first_page)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        
        ## paths for images 
        if getattr(sys, 'frozen', False):  # If running as .exe
            self.appPath = os.path.dirname(sys.executable)  # Directory where the .exe is located
        else:  # If running as a script
            self.appPath = os.path.dirname(os.path.abspath(__file__))

        self.nrgLogoPath = os.path.join(self.appPath,'resources','nrgLogo.png')
        self.flowLogo = os.path.join(self.appPath,'resources','flowLogo.png')

        #logo part
        self.LogoBar = QtWidgets.QWidget(self.first_page)
        self.LogoBar.setObjectName("LogoBar")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.LogoBar)
        self.horizontalLayout_2.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_2.setSpacing(-1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        #label for logo part
        self.label_8 = QtWidgets.QLabel(self.LogoBar)
        self.label_8.setAlignment(QtCore.Qt.AlignCenter)
        self.label_8.setObjectName("label_8")
        #styling logoBar
        self.LogoBar.setStyleSheet("""
        background-color: rgba(242, 232, 255, .6);
        border-radius: 5px;  
        """)

        self.pixmap = QPixmap(self.nrgLogoPath)
        self.label_8.setPixmap(QPixmap(self.nrgLogoPath))
        self.label_8.setFixedSize(50, 50)  #increase size to enlarge top bar
        self.label_8.setScaledContents(True)
        self.horizontalLayout_2.addWidget(self.label_8)
        # text below logo
        self.label_text = QtWidgets.QLabel(self.LogoBar)
        self.label_text.setAlignment(QtCore.Qt.AlignCenter)
        self.label_text.setStyleSheet("""
        color: rgb(32, 143, 42);  
        font-size: 15px; /*15px is good  */
        font-weight: bold;  /* Bold text */
        font-family: 'Arial', sans-serif;  /* Modern sans-serif font */
        padding: 10px;  /* Padding around the text */
        """)
        self.horizontalLayout_2.addWidget(self.label_text)
        self.gridLayout.addWidget(self.LogoBar, 0, 0, 1, 1)


        #drop down meter selection weidget
        self.MeterSelection = QtWidgets.QWidget(self.first_page)
        self.MeterSelection.setObjectName("MeterSelection")
        self.MeterSelection.setStyleSheet("""
        border: 1px solid rgba(100, 100, 100, 0.5);
        border-radius: 2px;  
        """)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.MeterSelection)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setSpacing(5)
        #self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        
        self.comboBox = QtWidgets.QComboBox(self.MeterSelection)
        self.comboBox.setMaxCount(11)
        self.comboBox.setIconSize(QtCore.QSize(10, 12))
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("Flow Meter 1")
        self.comboBox.addItem("Flow Meter 2")
        self.comboBox.addItem("Flow Meter 3")
        self.comboBox.addItem("Flow Meter 4")
        self.comboBox.addItem("Flow Meter 5")
        self.comboBox.addItem("Flow Meter 6")
        self.comboBox.addItem("Flow Meter 7")
        self.comboBox.addItem("Flow Meter 8")
        self.comboBox.addItem("Flow Meter 9")
        self.comboBox.addItem("Flow Meter 10")

        self.update_all_options()
        
        sep = SpacedItemDelegate()
        self.comboBox.setItemDelegate(sep)

        # Customizing the combo box
        self.comboBox.setStyleSheet("""
        QComboBox {
            background-color: rgba(255, 255, 255, 0.8);  
            border: 2px solid rgba(	75,0,130, 0.9); 
            border-radius: 5px;  
            padding: 5px;  
            color: rgba(0, 0, 0, 0.9);  
            font-size: 16px;  
            }
        QComboBox::drop-down {
            border: 2px solid rgba(	123,104,238,.9);  
            background-color: rgba(240, 240, 240, 0.9);  
            width: 30px;  /* Width of the dropdown arrow */
            }
        QComboBox::down-arrow {                                 
            image: url('resources/dropDown.png');                         
            width: 16px;  
            height: 16px;  
            subcontrol-origin: padding;  /* Position the arrow correctly */
            subcontrol-position: center;  /* Center the arrow */
            }
        """)
        self.horizontalLayout_3.addWidget(self.comboBox)


        self.timeLabel = QtWidgets.QLabel("Time")
        self.timeLabel.setAlignment(Qt.AlignCenter)
        self.timeLabel.setStyleSheet("""
        color: rgba(255, 0, 0, 1);  
        font-size: 23px;  
        font-weight: bold;  /* Bold text */
        font-family: 'Arial', sans-serif;  /* Modern sans-serif font */
        """)
        self.shiftLabel = QtWidgets.QLabel("Shift:")
        self.shiftLabel.setAlignment(Qt.AlignCenter)
        self.shiftLabel.setStyleSheet("""
        color: rgba(32, 143, 42, 1);  
        font-size: 20px;  
        font-weight: bold;  
        font-family: 'Arial', sans-serif;  /* Modern sans-serif font */
        """)
        self.status_label = QtWidgets.QLabel(f"Status")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
        font-size: 18px;  
        font-weight: bold;  
        font-family: 'Arial', sans-serif;  /* Modern sans-serif font */
        """)

        self.horizontalLayout_3.addWidget(self.timeLabel)
        self.horizontalLayout_3.addWidget(self.shiftLabel)
        self.horizontalLayout_3.addWidget(self.status_label)

        self.gridLayout.addWidget(self.MeterSelection, 0, 1, 1, 3)

        # menu bar containing push buttons section
        self.MenuBar = QtWidgets.QWidget(self.first_page)
        self.MenuBar.setObjectName("MenuBar")
        self.MenuBar.setStyleSheet("""
        background-color: rgba(248,248,255,1);
        border: 1px solid rgba(123,104,238,.3);
        border-radius: 3px;
        """)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.MenuBar)
        self.verticalLayout.setContentsMargins(6, -1, -6, -1)
        self.verticalLayout.setObjectName("verticalLayout")

        self.claib_button = QtWidgets.QPushButton(self.MenuBar)
        self.claib_button.setObjectName("calib_button")
        self.claib_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(50, 50, 50, 0.85);  /* Dark gray background */
                border: 5px solid rgba(230,230,250,.4);
                border-radius: 4px;  /* Slightly rounded corners for a subtle effect */
                color: white;  /* White text */
                font-size: 13px;  /* Smaller font size for a clean look */
                padding: 10px 20px;  /* Consistent padding for a menu-like feel */
                text-align: center;  /* Align text to the left */
                font-weight: 500;  /* Medium weight text for visibility */
            }
            QPushButton:hover {
                background-color: rgba(70, 70, 70, 0.95);  /* Lighter gray on hover */
                color: #00BFFF;  /* Highlight text in a modern blue shade */
            }
            QPushButton:pressed {
                background-color: rgba(30, 30, 30, 1);  /* Darker gray on click */
            }
            """)
        self.verticalLayout.addWidget(self.claib_button)

        self.pushButton_3 = QtWidgets.QPushButton(self.MenuBar)
        self.pushButton_3.setObjectName("pushButton_3")
        self.pushButton_3.setStyleSheet("""
            QPushButton {
                background-color: rgba(50, 50, 50, 0.85);  /* Dark gray background */
                border: 5px solid rgba(230,230,250,.4);
                border-radius: 4px;  /* Slightly rounded corners for a subtle effect */
                color: white;  /* White text */
                font-size: 13px;  /* Smaller font size for a clean look */
                padding: 10px 20px;  /* Consistent padding for a menu-like feel */
                text-align: center;  /* Align text to the left */
                font-weight: 500;  /* Medium weight text for visibility */
            }
            QPushButton:hover {
                background-color: rgba(70, 70, 70, 0.95);  /* Lighter gray on hover */
                color: #00BFFF;  /* Highlight text in a modern blue shade */
            }
            QPushButton:pressed {
                background-color: rgba(30, 30, 30, 1);  /* Darker gray on click */
            }
            """)
        self.verticalLayout.addWidget(self.pushButton_3)

        self.pushButton_4 = QtWidgets.QPushButton(self.MenuBar)
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_4.setStyleSheet("""
            QPushButton {
                background-color: rgba(50, 50, 50, 0.85);  /* Dark gray background */
                border: 5px solid rgba(230,230,250,.4);
                border-radius: 4px;  /* Slightly rounded corners for a subtle effect */
                color: white;  /* White text */
                font-size: 13px;  /* Smaller font size for a clean look */
                padding: 10px 20px;  /* Consistent padding for a menu-like feel */
                text-align: center;  /* Align text to the left */
                font-weight: 500;  /* Medium weight text for visibility */
            }
            QPushButton:hover {
                background-color: rgba(70, 70, 70, 0.95);  /* Lighter gray on hover */
                color: #00BFFF;  /* Highlight text in a modern blue shade */
            }
            QPushButton:pressed {
                background-color: rgba(30, 30, 30, 1);  /* Darker gray on click */
            }
            """)
        self.verticalLayout.addWidget(self.pushButton_4)

        self.pushButton_5 = QtWidgets.QPushButton(self.MenuBar)
        self.pushButton_5.setObjectName("pushButton_5")
        self.pushButton_5.setStyleSheet("""
            QPushButton {
                background-color: rgba(50, 50, 50, 0.85);  /* Dark gray background */
                border: 5px solid rgba(230,230,250,.4);
                border-radius: 4px;  /* Slightly rounded corners for a subtle effect */
                color: white;  /* White text */
                font-size: 13px;  /* Smaller font size for a clean look */
                padding: 10px 20px;  /* Consistent padding for a menu-like feel */
                text-align: center;  /* Align text to the left */
                font-weight: 500;  /* Medium weight text for visibility */
            }
            QPushButton:hover {
                background-color: rgba(70, 70, 70, 0.95);  /* Lighter gray on hover */
                color: #00BFFF;  /* Highlight text in a modern blue shade */
            }
            QPushButton:pressed {
                background-color: rgba(30, 30, 30, 1);  /* Darker gray on click */
            }
            """)
        self.verticalLayout.addWidget(self.pushButton_5)
        self.gridLayout.addWidget(self.MenuBar, 1, 0, 2, 1)

        #dashboard or self.setV,self.curV,total section
        self.Data = QtWidgets.QWidget(self.first_page)
        self.Data.setObjectName("Data")
        self.Data.setStyleSheet("""
        background-color: rgba(248,248,255,1);
        border: 1px solid rgba(123,104,238,.3);
        border-radius: 3px;
        """)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.Data)
        self.verticalLayout_2.setContentsMargins(10, 5, -1, 5)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")

        #self.setV styles
        self.label = QtWidgets.QLabel(self.Data)
        self.label.setObjectName("label")
        self.label.setStyleSheet("""
        background-color: rgba(240,255,255,.4);
        border: None;
        color: rgba(10,0,10,.9);
        font-weight: 200;
        font-size: 17px; 
        """)
        self.verticalLayout_2.addWidget(self.label)

        self.lcdNumber = QtWidgets.QLCDNumber(self.Data)
        self.lcdNumber.setDigitCount(8)
        self.lcdNumber.setProperty("intValue", 0)    
        self.lcdNumber.setObjectName("lcdNumber")
        self.lcdNumber.setDigitCount(12)
        self.lcdNumber.setStyleSheet("""
        background-color: rgba(255,255,255,1);
        border: 1px solid rgba(0,0,0,1);
        font-weight: bold;
        font-size: 18px;
        color: rgba(10,10,15,1);
        """)
        self.verticalLayout_2.addWidget(self.lcdNumber)
        
        #edit self.setV button
        self.pushButton = QtWidgets.QPushButton(self.Data)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())

        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setIconSize(QtCore.QSize(5, 5))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setStyleSheet("""
            QPushButton {
                background-color: rgba(50, 50, 50, 0.85);  /* Dark gray background */
                border: 5px solid rgba(230,230,250,.4);
                border-radius: 4px;  /* Slightly rounded corners for a subtle effect */
                color: white;  /* White text */
                font-size: 12px;  /* Smaller font size for a clean look */
                padding: 10px 20px;  /* Consistent padding for a menu-like feel */
                text-align: center;  /* Align text to the left */
                font-weight: 500;  /* Medium weight text for visibility */
            }
            QPushButton:hover {
                background-color: rgba(70, 70, 70, 0.95);  /* Lighter gray on hover */
                color: #00BFFF;  /* Highlight text in a modern blue shade */
            }
            QPushButton:pressed {
                background-color: rgba(30, 30, 30, 1);  /* Darker gray on click */
            }
            """)
        self.verticalLayout_2.addWidget(self.pushButton, 0, QtCore.Qt.AlignHCenter)


        self.label_4 = QtWidgets.QLabel(self.Data)
        self.label_4.setObjectName("label_4")
        self.label_4.setStyleSheet("""
        background-color: rgba(240,255,255,.4);
        border: None;
        color: rgba(10,0,10,.9);
        font-weight: 200;
        font-size: 17px; 
        """)
        self.verticalLayout_2.addWidget(self.label_4)

        self.lcdNumber_2 = QtWidgets.QLCDNumber(self.Data)
        self.lcdNumber_2.setDigitCount(8)
        self.lcdNumber_2.setProperty("intValue", 0)  
        self.lcdNumber_2.setObjectName("lcdNumber_2")
        self.lcdNumber_2.setDigitCount(12)
        self.lcdNumber_2.setStyleSheet("""
        background-color: rgba(255,255,255,1);
        border: 1px solid rgba(0,0,0,1);
        font-weight: bold;
        font-size: 18px;
        color: rgba(10,10,15,1);
        """)
        self.verticalLayout_2.addWidget(self.lcdNumber_2)

        self.pushButton_2 = QtWidgets.QPushButton(self.Data)
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_2.setStyleSheet("""
            QPushButton {
                background-color: rgba(50, 50, 50, 0.85);  /* Dark gray background */
                border: 5px solid rgba(230,230,250,.4);
                border-radius: 4px;  /* Slightly rounded corners for a subtle effect */
                color: white;  /* White text */
                font-size: 13px;  /* Smaller font size for a clean look */
                padding: 10px 20px;  /* Consistent padding for a menu-like feel */
                text-align: center;  /* Align text to the left */
                font-weight: 500;  /* Medium weight text for visibility */
            }
            QPushButton:hover {
                background-color: rgba(70, 70, 70, 0.95);  /* Lighter gray on hover */
                color: #00BFFF;  /* Highlight text in a modern blue shade */
            }
            QPushButton:pressed {
                background-color: rgba(30, 30, 30, 1);  /* Darker gray on click */
            }
            """)
        self.verticalLayout_2.addWidget(self.pushButton_2, 0, QtCore.Qt.AlignHCenter)

        self.label_3 = QtWidgets.QLabel(self.Data)
        self.label_3.setObjectName("label_3")
        self.label_3.setStyleSheet("""
        background-color: rgba(240,255,255,.4);
        border: None;
        color: rgba(10,0,10,.9);
        font-weight: 200;
        font-size: 17px; 
        """)
        self.verticalLayout_2.addWidget(self.label_3)


        self.lcdNumber_3 = QtWidgets.QLCDNumber(self.Data)
        self.lcdNumber_3.setDigitCount(8)
        self.lcdNumber_3.setObjectName("lcdNumber_3")
        self.lcdNumber_3.setDigitCount(12)
        self.lcdNumber_3.setStyleSheet("""
        background-color: rgba(255,255,255,1);
        border: 1px solid rgba(0,0,0,1);
        font-weight: bold;
        font-size: 18px;
        color: rgba(10,10,15,1);
        """)
        self.verticalLayout_2.addWidget(self.lcdNumber_3)
        self.gridLayout.addWidget(self.Data, 1, 1, 2, 1)

        #percentage usage meter section
        self.meterSection = QtWidgets.QWidget(self.first_page)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.meterSection)

        self.Meter = RoundProgressbar(
            parent=self.meterSection,  # Use the central widget as the parent
            color=QColor("darkblue"),
            size=100,
            thickness=18,
            value=80,
            maximum=100,
            round_edge=True,
            bg_circle_color=QColor("cyan"),
            fill_bg_circle=False,
            percent_color=QColor("darkblue")
        )
        self.verticalLayout.addWidget(self.Meter)
        self.gridLayout.addWidget(self.meterSection, 1, 2, 2, 2)
        

        #graph plotting section
        self.graph = QtWidgets.QWidget(self.first_page)
        self.graph.setObjectName("graph")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.graph)
        self.verticalLayout_4.setObjectName("verticalLayout_4")

        self.plot_widget = pg.PlotWidget()
        self.verticalLayout_4.insertWidget(0, self.plot_widget)
        
        self.gridLayout.addWidget(self.graph, 3, 0, 1, 4)
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 2)
        self.gridLayout.setColumnStretch(2, 1)
        self.gridLayout.setColumnStretch(3, 1)
        self.gridLayout.setRowStretch(1, 2)
        self.gridLayout.setRowStretch(2, 1)
        self.gridLayout.setRowStretch(3, 2)

        '''Switching between frames'''

        self.frameN = QtWidgets.QFrame(self.first_page)
        self.frameN.setGeometry(700, 140, 100, 100)  # Set position and size
        self.frameN.setStyleSheet("background-color: rgb(255, 255, 255);")  # Optional: Give the self.frameN a color
        self.frameN.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frameN.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frameN.setObjectName("customFrameN")

        self.frameB = QtWidgets.QFrame(self.second_page)
        self.frameB.setGeometry(0, 140, 100, 100)  # Set position and size
        self.frameB.setStyleSheet("background-color: rgba(240,255,255,.1);")  # Optional: Give the self.frameN a color
        self.frameB.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frameB.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frameB.setObjectName("customFrameB")
        #self.frameN.show()

        # Create an invisible next button on the self.frameN
        self.next_button = QtWidgets.QPushButton(self.frameN)
        self.next_button.setGeometry(QtCore.QRect(0, 0, 100, 100))  # Match button size to self.frameN
        self.next_button.setStyleSheet("background: transparent; border: none;")  # Invisible style
        self.next_button.setObjectName("invisibleButton")

        # # Connect the button to a function
        #implemented in main window for pass protection
        #self.next_button.clicked.connect(self.next_page)

        #bcak button
        self.back_button = QtWidgets.QPushButton(self.frameB)
        self.back_button.setText('⇦')
        self.back_button.setStyleSheet("""
            QPushButton {
                background: transparent; 
                border: none;
                font-size: 60px;
                font-weight: bold;
                color: darkblue;
            }""")
        self.back_button.setGeometry(QtCore.QRect(0, 0, 100, 100))  # Match button size to self.frameN
        self.back_button.setObjectName("backButton")
        # self.back_button.clicked.connect(self.back)


        self.central_stack_widget.addWidget(self.first_page)
        self.central_stack_widget.addWidget(self.second_page)
        MainWindow.setCentralWidget(self.central_stack_widget)

        self.retranslateUi(MainWindow)
        #QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def styleLabel(self,label,s,idx):
        label.setStyleSheet("""
        background-color: rgba(240,255,255,.9);
        border: None;
        color: rgba(10,0,10,.9);
        font-weight: 200;
        font-size: 30px; 
        """)
        if s:
            label.setText(f"                    Meter:{idx+1}")
        else:
            label.setText(f"                    Meter:{chr(64+idx+1)}")
        

    # def back(self):
    #     self.central_stack_widget.setCurrentWidget(self.first_page)
    
    def update_all_options(self): #iters through slaves that are active when app started
        for i,state in enumerate(active):
            if not state:
                self.comboBox.setItemData(i, QtGui.QColor('red'), QtCore.Qt.ForegroundRole)
                self.comboBox.model().item(i).setEnabled(False)
            else:
                self.comboBox.setItemData(i, QtGui.QColor('Green'), QtCore.Qt.ForegroundRole)
                self.comboBox.model().item(i).setEnabled(True)
                

    def update_combobox(self,idx:int,state:bool): # item id  = slave_id -1
        self.comboBox.setItemData(int(idx), QtGui.QColor('red'), QtCore.Qt.ForegroundRole)
        self.comboBox.model().item(int(idx)).setEnabled(bool(state))
        


    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", f"Smart Flow Meter"))
        MainWindow.setWindowIcon(QIcon(self.flowLogo))
        self.label_text.setText(_translate("MainWindow", "Powered by\nNRG RnD"))
        self.claib_button.setText(_translate("MainWindow", "Calibrate"))
        self.pushButton_3.setText(_translate("MainWindow", "Add Demand"))
        self.pushButton_4.setText(_translate("MainWindow", "Reset Password"))
        self.pushButton_5.setText(_translate("MainWindow", "Useage History"))
        self.label.setText(_translate("MainWindow", "SET VALUE(Litre)"))
        self.pushButton.setText(_translate("MainWindow", "Edit SetV"))
        self.label_4.setText(_translate("MainWindow", "CURRENT USAGE(Litre)"))
        self.pushButton_2.setText(_translate("MainWindow", "  Reset   "))
        self.label_3.setText(_translate("MainWindow", "TOTAL USAGE(Lakh Litre)"))

"""Main app class """
class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainApp, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.dm = DataManager()
        self.tym_obj = datetime.now()
        self.lock = Lock() # threding safety
        self.initialize_data() ## password and total
        self.plot_data = self.ui.plot_widget.plot(pen=pg.mkPen('r', width=2)) ##this for graph pen setting

    # App paths 
        if getattr(sys, 'frozen', False):  # If running as .exe
            self.base_path = os.path.dirname(sys.executable) 
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        self.usagePath = os.path.join(self.base_path,'resources','usage.xlsx')

        '''before production change the client , 19200,8N1'''
    # Initializing Communication
        self.client = mb(port=com, baudrate=19200, stopbits=1, timeout=.1,retries=2)
        if not self.client.connect():
            self.feedBack("Failed to connect to the Modbus slave.")
            time.sleep(10)
            exit()

        self.calib = CalibrationWindow(client=self.client,active = active) ##thid is for faster loading of calibration

    # slave id for diferrent meters::initialized to 1 :: updates when selected from combobox
        self.slave_id = 1
        self.ui.comboBox.currentIndexChanged.connect(self.update_slave_id)

    # timers setion
     # timer to poll Modbus data every 100 second
        self.timer = QtCore.QTimer(self)
        #use 'if' to se which page is active
        self.timer.timeout.connect(self.update_data_func)
        self.interv_poll = 50
        self.timer.start(self.interv_poll)  # Update every 100 ms (.1 second)

     # timer for refreshing connection :: checking the active status by pinging
        self.refresh = QtCore.QTimer(self)
        self.refresh.timeout.connect(self.ui.update_all_options)
        self.interv_refresh = 500
        self.refresh.start(self.interv_refresh)

        self.ui.pushButton.clicked.connect(self.edit_set_value)
        self.ui.pushButton_2.clicked.connect(self.reset_current_usage)
        self.ui.pushButton_3.clicked.connect(self.add_demand)
        self.ui.pushButton_4.clicked.connect(self.reset_password)
        self.ui.pushButton_5.clicked.connect(self.show_usage_history)
        self.ui.claib_button.clicked.connect(self.calibration)
        self.ui.next_button.clicked.connect(self.next_page)
        self.ui.back_button.clicked.connect(self.back)


      #timer to update data in a seperate thread
        self.save_data_timer = QtCore.QTimer(self)
        self.save_data_timer.timeout.connect(self.update_all_data)
        self.interv_save = 10*1000
        self.save_data_timer.start(self.interv_save) #######################################################

    # new threading (new thread will stop timer and quickly collect all curV and then start timer, after that saved)
      #instantiating workers
        self.worker = Worker(client=self.client, total=self.total,feedBack=self.feedBack,ui = self.ui)
        self.uploader = Uploader(state=self.ui.status_label)

      #thread perameters
        self.thread_w = QtCore.QThread()
        self.worker.moveToThread(self.thread_w)

        self.uploader_thread = QtCore.QThread()
        self.uploader.moveToThread(self.uploader_thread)

      #signals and slots for the threads
        self.worker.saved.connect(self.start_timer) # starts a timer here for polling single slave
        self.worker.start_uploading.connect(self.uploader.on_upload_signal)

      # starting the threads
        self.thread_w.start()
        self.uploader_thread.start()

    def back(self):
        self.ui.central_stack_widget.setCurrentWidget(self.ui.first_page)
        self.start_dump()

    def next_page(self):
        x = self.getPassword()
        if x == 'c':
            self.stop_dump()
            self.ui.central_stack_widget.setCurrentWidget(self.ui.second_page)
        elif x=='x':
            pass   
        else:
            self.showErrorDialog()
        self.start_dump()

    def update_data_func(self):
        if self.ui.central_stack_widget.currentIndex()==0:
            self.update_data()## first page
        else:
            self.update_data_2()## second page
            
           
    def stop_dump(self): # this is for stoppping all the processing
        self.timer.stop()
        self.refresh.stop()
        self.save_data_timer.stop()

        self.thread_w.quit()
        self.uploader_thread.quit()

    def start_dump(self): # this is for starting all the processing
        self.timer.start(self.interv_poll)
        self.refresh.start(self.interv_refresh)
        self.save_data_timer.start(self.interv_save)

        self.thread_w.start()
        self.uploader_thread.start()

    def calibration(self):
        self.client.close()
        self.stop_dump()
    
        # calib = CalibrationWindow(client=self.client)

        self.calib.calib_data.connect(self.update_calib)
        self.calib.exec_()
        self.client.close()

        self.start_dump()       

    def update_calib(self,data): #### this is important
        global calib_reg
        calib_reg = data
        dm = DataManager()
        dm.setCalib(calib_reg)


    @QtCore.pyqtSlot()
    def update_all_data(self): ## this will stop timer and start worker class
        self.timer.stop()
        self.worker.update.emit() ## command to start updating values

    @QtCore.pyqtSlot()
    def start_timer(self):
        self.timer.start(self.interv_poll)
        self.worker.start_saving.emit()

    def initialize_data(self):
        global calib_reg

        self.password = self.dm.getPass()
        self.total = self.dm.getTotal() ### get previous day's value
        self.Ctotal = np.array([.1]*10,dtype=np.float32)#[1]*10 ### current day's value will be updated from here
        self.setV =  np.ones(10,dtype=np.int32)#[1]*10
        self.curV = np.ones(10,dtype=np.int32)#[1]*10
        calib_reg = self.dm.getCalib()

    def is_time_between(self, start: time, end: time, check_time: time) -> bool:
        if start < end:  
            return start <= check_time <= end
        else:  
            return check_time >= start or check_time <= end

    def show_usage_history(self):
            # Fixed path for the Excel file
            x = self.getPassword()
            if x == 'c' or x == 'm':
                self.stop_dump()
                file_path =os.path.join(self.base_path,'resources','RexUsage.xlsx')
                div = 3 if x=='c' else 1
                try:
                    lock = Lock()
                    with lock:
                        df = pd.read_excel(file_path,sheet_name=f"Sheet{self.slave_id}")
                    dialog = QDialog(self)
                    dialog.setWindowTitle("Usage History")
                    dialog.setFixedSize(700,480)
                    layout = QVBoxLayout(dialog)

                    # Creating a table widget
                    table = QTableWidget()
                    table.setRowCount(df.shape[0])
                    table.setColumnCount(df.shape[1])
                    table.setHorizontalHeaderLabels(df.columns)
                    table.setShowGrid(True)
                    table.setAlternatingRowColors(True)

                    xat = -1 # tracks todays date
                    for i in range(df.shape[0]):
                        for j in range(df.shape[1]):
                                value = df.iat[i,j]
                                if isinstance(value, str):
                                    table.setItem(i, j, QTableWidgetItem(value))
                                    if value == datetime.now().strftime('%d/%m/%Y'):
                                        xat = i
                                elif j == 1:  # Specific logic for column 1
                                    value = (value / lakh).round(4) if i == xat else (value / (lakh * div)).round(4)
                                    table.setItem(i, j, QTableWidgetItem(str(value)))
                                else:
                                    adjusted_value = np.int64(value / div) if not xat==i else value
                                    table.setItem(i, j, QTableWidgetItem(str(adjusted_value)))

                    # Populating the table with data
                    # for i in range(df.shape[0]):
                    #     for j in range(df.shape[1]):
                    #         if isinstance(df.iat[i, j],str):
                    #             table.setItem(i, j, QTableWidgetItem(df.iat[i, j]))
                    #             if df.iat[i,j] == datetime.now().strftime('%d/%m/%Y'):
                    #                 xat = i
                    #         elif i == xat:
                    #             table.setItem(i, j, QTableWidgetItem(str((df.iat[i, j]/lakh).round(4)))) if j==1 else table.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))
                    #         else:
                    #             table.setItem(i, j, QTableWidgetItem(str((df.iat[i, j]/(lakh*3)).round(4)))) if j==1 else table.setItem(i, j, QTableWidgetItem(str(np.int64(df.iat[i, j]/div))))

                    # Add the table to the layout and setV the layout for the dialog
                    layout.addWidget(table)
                    dialog.setLayout(layout)

                    # Show the dialog
                    dialog.exec_()

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load History:\n{e}")
            elif x=='x':
                pass   
            else:
                self.showErrorDialog()
                pass
            self.start_dump()
    
    def split_32bit_number(self,num):
        try:
            if (0 <= num < 0xFFFFFFFF):
                upper_16 = (num >> 16) & 0xFFFF
                lower_16 = num & 0xFFFF 
                return upper_16, lower_16
            elif num == 0:
                return 0,0
        except:
            self.feedBack("Splitting Value error")
            return None,None
    
    def reset_current_usage(self):
        try:
            x = self.getPassword()
            if x == 'c':
                self.timer.stop()
                address =4
                value = 4
                response = self.client.write_register(address,value,slave=self.slave_id)
                if response.isError():
                    self.feedBack(f"Error : {response}")
                else:
                    self.feedBack(f"Reset done")
            elif x=='x':
                self.client.close()
                pass   
            else:
                self.showErrorDialog()
                self.client.close()
                pass
        finally:
            self.timer.start(self.interv_poll)
            self.client.close()

    def getPassword(self):
        self.timer.stop()
        dlg = QInputDialog(self)
        text, ok = dlg.getText(None, "Smart Flow Meter", "Enter your Current Password", 
                                        QLineEdit.Password)
        if ok and text:
            if self.password == text:
                self.timer.start(self.interv_poll)
                return 'c'
            elif text == 'ostadMAHBUB':
                self.timer.start(self.interv_poll)
                return 'm'
            else:
                self.timer.start(self.interv_poll)
                return 'i'
        else: 
            self.timer.start(self.interv_poll)
            return 'x'
                    
    def showErrorDialog(self):
        msg = QMessageBox()
        msg.setWindowTitle("Smart Flow Meter")
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Incorrect Password")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def feedBack(self,mssg):
        obj = QMessageBox()
        obj.setWindowTitle("Smart Flow Meter")
        obj.setIcon(QMessageBox.Information)
        obj.setText(mssg)
        obj.setStandardButtons(QMessageBox.Ok)
        obj.exec_()
    
    def getText(self):
        self.timer.stop()
        value, ok = QInputDialog.getText(None,"Smart Flow Meter", "Enter New Password", 
                                        QLineEdit.Normal)
        if ok and len(value)>1:
            self.timer.start(self.interv_poll)
            return value
        else:
            self.timer.start(self.interv_poll)
            return None
            
    def edit_set_value(self):
        x = self.getPassword()
        if x == 'c':
            self.stop_dump()
            try:
                dlg = CInputDialog(self)
                num,value = dlg.getInteger() # value here determines the state real or subreal
                if  num > 999999999: 
                    num = 999999999
                setV = np.uint32(num) * calib_reg[self.slave_id-1]

                if  setV > 999999999: 
                    setV = 999999999

                up, low = self.split_32bit_number(np.uint32(setV))
                if up==None or low==None or up=='' or low=='':
                    self.timer.start(self.interv_poll)
                    return
                try:
                    address = 4
                    response1 = self.client.write_register(address, value, slave=self.slave_id) 
                    time.sleep(1) 
                    if response1.isError():
                        self.feedBack(f"Error modifier at {self.slave_id} : \n {response1}")
                    else:
                        try:
                            responseU = self.client.write_register(8,up, slave=self.slave_id) 
                            time.sleep(1) 
                            responseL = self.client.write_register(9, low, slave=self.slave_id)  
                            if responseU.isError() or responseL.isError() :
                                self.feedBack(f"Error writting to registers :\n{responseU}\n{responseL}")
                            else:
                                time.sleep(1)
                                address = 4
                                value = 0
                                response = self.client.write_register(address, value, slave=self.slave_id)
                                if not response.isError():
                                    self.feedBack("Succesfully Updated")
                                
                        except:
                            self.feedBack("Try again")
                finally:
                    self.client.close()
            except Exception as e:
                self.feedBack(f"Value Error{e}") 
                self.client.close()
                
        elif x=='x':
            self.client.close()
               
        else:
            self.showErrorDialog()
            self.client.close()
        self.start_dump()
    
    def add_demand(self):
        x = self.getPassword()
        if(x=='c'):
            self.stop_dump()

            dlg = CInputDialog(self)
            num = np.int32(dlg.getInteger()[0]) * calib_reg[self.slave_id-1]
            if num > 9999999 : num = 9999999
            upper, lower = self.split_32bit_number(np.uint32(num))
            if upper==None or lower==None or upper=='' or lower=='':
                self.timer.start(self.interv_poll)
                return
            try:
                address = 4
                value = 3
                time.sleep(1) 
                response1 = self.client.write_register(address, value, slave=self.slave_id)  
                if response1.isError():
                    self.feedBack(f"Error modifier at {self.slave_id}:{response1}")
                else:
                    try:
                        addressU = 6
                        responseU = self.client.write_register(addressU,upper, slave=self.slave_id)  # unit is the slave ID
                        addressL = 7
                        time.sleep(1)
                        responseL = self.client.write_register(addressL, lower, slave=self.slave_id)  
                        if responseU.isError() or responseL.isError() :
                            self.feedBack(f"Error writing to registers:/n{responseU}/n{responseL}")
                        else:
                            address = 4
                            value = 0
                            time.sleep(1) 
                            response = self.client.write_register(address, value, slave=self.slave_id)
                            if not response.isError():
                                self.feedBack("Successfully Updated")
                            
                    except:
                        self.feedBack("Value error")

            finally:
                self.client.close()
        elif x == 'x':
            self.client.close()
            pass   
        else:
            self.showErrorDialog()
            self.client.close()
            pass
        self.start_dump()

    def reset_password(self):
        dm = DataManager()
        x = self.getPassword() 
        if(x=='c'):
            self.timer.stop()
            passw = self.getText()
            if passw is not None:
                self.password = passw
                dm.pushPass(self.password)
                self.feedBack("Password Updated Successfully")
            else:
                pass 
        elif x=='x':
            pass
        else:
            self.showErrorDialog()
        self.timer.start(self.interv_poll)

    def update_slave_id(self, index):
        self.slave_id = index + 1

    def update_data_2(self):
        #poll all 20 meters to read flow range
        #self.client.close()
        for row in range(10):
            for col in range(2):
                if col == 0:
                    try: ## for smart meter
                        if active[row]:
                            response = self.client.read_holding_registers(address=0, count=4, slave=row+1)
                            val_s = int((response.registers[2] * 65536 + response.registers[3]) / calib_reg[row])
                            self.ui.lcd_displays[row][col].display(val_s)
                    except:
                        pass
                    
                elif col==1:
                    try: ## for analogue meter
                        pass
                    except:
                        pass
                    self.ui.lcd_displays[row][col].display(row)
        self.start_dump()
        

        #show it on display 
    
    def update_data(self):
        try:
            global shift
            global active
            global calib_reg

            response = self.client.read_holding_registers(address=0, count=4, slave=self.slave_id)
            if not response.isError():
                ##setV value from eeprom
                register_0 = response.registers[0]
                register_1 = response.registers[1]

                ##pulse count from arduino::pulseCount-prevPulseCount
                register_2 = response.registers[2]
                register_3 = response.registers[3]

                # setting that slave is ok
                active[self.slave_id-1] = True

                # Combine the two 16-bit values into a single 32-bit value
                self.setV[self.slave_id-1] = int((register_0 * 65536 + register_1) / calib_reg[self.slave_id - 1])
                self.curV[self.slave_id-1] = int((register_2 * 65536 + register_3) / calib_reg[self.slave_id-1])
                self.Ctotal[self.slave_id-1] = self.total[self.slave_id-1] + self.curV[self.slave_id-1]/ lakh #cumilitive total from 1969

                # Update the LCD displays
                self.ui.lcdNumber.display(self.setV[self.slave_id-1])
                self.ui.lcdNumber_2.display(self.curV[self.slave_id-1])
                self.ui.lcdNumber_3.display(f"{self.Ctotal[self.slave_id-1]:.2f}") ### -1 because of array

                # data pushing for circular meter
                if self.setV[self.slave_id-1]<=0:
                    self.setV[self.slave_id-1]=1
                self.ui.Meter.set_maximum(self.setV[self.slave_id-1]) 
                self.ui.Meter.set_value(self.curV[self.slave_id-1])

                self.plot_data.setData(range(24),graph_hour[:,self.slave_id-1])

                self.tym = datetime.now().strftime("%H:%M:%S")
                self.ui.timeLabel.setText(str(datetime.now().strftime("%I:%M %p")))
                tym_object = datetime.strptime(self.tym, "%H:%M:%S").time()

                with self.lock:
                    if self.is_time_between(tyme(6,1),tyme(14,0),tym_object):
                        self.ui.shiftLabel.setText("Shift : A")
                        shift = 0
                    elif self.is_time_between(tyme(14,1),tyme(22,0),tym_object):
                        self.ui.shiftLabel.setText("Shift : B")
                        shift = 1
                    elif self.is_time_between(tyme(22,1),tyme(6,0),tym_object):
                        self.ui.shiftLabel.setText("Shift : C")
                        shift = 2
                    else: 
                        self.ui.shiftLabel.setText("Shift : ")  
                        shift = -1  

                    #reset functionalities
                    if  self.tym_obj.time().hour >= 6  and self.tym_obj.time().hour < 18 and not self.dm.getReset() : ######### resetting everything at 6 am to 6 pm
                        self.day_reset()
                        self.dm.pushreset(1)
                    if (self.tym_obj.time().hour > 18 or self.tym_obj.time().hour < 6)  and self.dm.getReset() :  #18 to 6
                        self.dm.pushreset(0)

            else:
                active[self.slave_id-1] = False
                self.ui.comboBox.setCurrentIndex(np.argmax(active==True)) #
               
        except Exception as e:
            #self.feedBack(f"Exception occurred: {e}")
            pass
        #    exit()
        #self.start_dump()

    def day_reset(self):
        self.timer.stop()
        self.refresh.stop()
        self.save_data_timer.stop()

        self.thread_w.quit()
        self.uploader_thread.quit()

        for i,state in enumerate(active): ########################################################################################
            if state:
                try:
                    address =4
                    value = 5
                    response = self.client.write_register(address,value,slave=i+1)
                    if response.isError():
                        self.feedBack(f"Error : {response}")
                    else:
                        self.feedBack(f"Reset done") 
                finally:
                    self.client.close()
        self.dm.pushLive([0,0,0,0,0,0,0,0,0,0])
        self.dm.resetHour()

        self.timer.start(self.interv_poll)
        self.refresh.start(self.interv_refresh)
        self.save_data_timer.start(self.interv_save)

        self.thread_w.start()
        self.uploader_thread.start()

    def closeEvent(self, event):
        """Handle application close event."""
        self.thread_w.quit()  # Quit Worker1 thread
        self.thread_w.wait()  # Wait for the thread to finish

        self.uploader_thread.quit()
        self.uploader_thread.wait()
        super().closeEvent(event)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ui.frameN.setGeometry(self.width()-self.width()//15,self.height()//2-self.height()//10,self.width()//15,self.height()//10)
        self.ui.frameB.setGeometry(self.width()-self.width(),self.height()//2-self.height()//10,self.width()//15,self.height()//10)
    
"""offline process class """  
class Worker(QtCore.QObject):
    # Signal to send data to the main application
    running = True # if loop needed so that it can be controlled from here
    update = QtCore.pyqtSignal() # signal for polling all the slave from main app class
    saved = QtCore.pyqtSignal() # signal for starting the timer:: self.timer ; for single polling in main app class 
    start_saving = QtCore.pyqtSignal() # after polling all data signal to start local saving
    start_uploading = QtCore.pyqtSignal(dict) # signal for uploader to receive and upload 

    def __init__(self, client, total,feedBack,ui):
        super().__init__()
        self.ui = ui
        self.feedBack = feedBack
        self.client = client
        self.total = total
        self.setV = np.ones(10,dtype=np.uint32) #[1] * 10  #change the type if it shows emitting problem
        self.curV = np.ones(10,dtype=np.uint32) #[1] * 10
        #self.Ctotal = np.ones(10,dtype=np.uint32) #[1] * 10
        self.Ctotal = np.array([.1]*10,dtype=np.float32)
        self.demand = np.ones(10,dtype=np.uint16) #[0] *10
        self.shift_data = [[0 for _ in range(3)] for _ in range(10)] # zeros 10x3 
        self.tym_obj = datetime.now()

        self.running = True  # Control flag to stop the worker gracefully
        self.lock = QtCore.QMutex()  # Mutex for thread-safe data access
        self.dm = DataManager()
        self.live = self.dm.getLive() # live data is the previous pulse count when app is opened  
        
        global graph_hour
        graph_hour = self.dm.getHour()
        self.initial_active_slaves = np.where(active==True)[0] # numer of 1s in active array

        self.update.connect(self.start_updating_data) # signal for polling all the slave from main app
        self.start_saving.connect(self.save_data) # signal for saving data after polling is finished

    @QtCore.pyqtSlot()
    def start_updating_data(self):
        for i in self.initial_active_slaves: ## i is the idx of active slaves
            if active[i]:
                self.update_data(i+1) #####################################################################
            else:
                self.check_response(i)
        self.saved.emit() ## get back start polling that's it

    def check_response(self,idx): # checks response if any initial slave goes offline
        response = self.client.read_holding_registers(address=0, count=1, slave=int(idx+1))
        if not response.isError():
            active[idx] = True
              
   
    def update_data(self, slave_id):
        try:
            self.tym_obj = datetime.now() # to get the latest date and time

            global active

            response = self.client.read_holding_registers(address=0, count=8, slave=int(slave_id)) ########################
            if not response.isError():
                # Extract and process register values
                register_0 = response.registers[0]
                register_1 = response.registers[1]
                register_2 = response.registers[2]
                register_3 = response.registers[3]
                register_6 = response.registers[6]
                register_7 = response.registers[7]

                # setValue  = int(((register_0 * 65536) + register_1) / calib_reg[slave_id - 1])
                # current_value = int(((register_2 * 65536) + register_3) / calib_reg[slave_id - 1])
                # demand = int(((register_6 * 65536) + register_7) / calib_reg[slave_id - 1])
                setValue  = np.uint32(((register_0 * 65536) + register_1) / calib_reg[slave_id - 1])
                current_value = np.uint32(((register_2 * 65536) + register_3) / calib_reg[slave_id - 1])
                demand = np.uint16(((register_6 * 65536) + register_7) / calib_reg[slave_id - 1])

                with QtCore.QMutexLocker(self.lock):  # Ensure thread-safe updates
                    self.curV[slave_id - 1] = current_value 
                    self.setV[slave_id - 1] = setValue 
                    ### substracting so that closing and opening app does not add up values
                    # Ctotal is cumilitive total for saving in data.pkl
                    #self.l = np.round((current_value - np.uint32(self.live[slave_id - 1]))/lakh,2)
                    if current_value>self.live[slave_id - 1]:
                        self.l = np.round((current_value - np.uint32(self.live[slave_id - 1]))/lakh,2)
                    else:
                        self.l = np.round(self.live[slave_id - 1]/lakh,2)
                    self.Ctotal[slave_id - 1] = self.total[slave_id - 1] + self.l
                    self.demand[slave_id - 1] = demand 

                active[slave_id-1] = True ############################################################
                
            else:
                active[slave_id-1] = False ###########################################################
                
        except Exception as e:
            self.feedBack(f"Error updating meter {slave_id}: {e}")

    @QtCore.pyqtSlot()
    def save_data(self):
        #print(datetime.now().time())
        global graph_hour

        self.dm.pushLive(self.curV)
        if np.amax(self.Ctotal) >= np.amax(self.total): # self.total is previous Ctotal
            self.dm.pushTotal(self.Ctotal)  #curent cumilitive total push
            

        for id,state in enumerate(active): #xl logging
            if state: # if slave if acctive write
                if shift != -1:
                    self.shift_data[id][shift] = self.curV[id]
                #self.dm.pushValue(id+1,int(self.curV[id]/3),int(self.shift_data[id][0]/3),int(self.shift_data[id][1]/3),int(self.shift_data[id][2]/3),self.demand[id])
                self.dm.pushValue(id+1,self.curV[id],self.shift_data[id][0],self.shift_data[id][1],self.shift_data[id][2],self.demand[id],sw=0)

      # graph register       
        self.dm.pushHour(self.tym_obj.time().hour,self.curV)
        graph_hour = self.dm.getHour()

     #sending data to uploader
        #print("emitting data")
        self.start_uploading.emit({
            'setV':self.setV,
            'curV':self.curV,
            'Ctotal':self.Ctotal,
            'demand':self.demand,
            'shift':self.shift_data
        })

        #print(datetime.now().time())

"""online process class """                  
class Uploader(QtCore.QObject):
    auth_flag = False
    def __init__(self, state):
        super().__init__()
        self.dm = DataManager()
        self.state = state
        try:
            self.sheet = self.dm.auth_access() # authenticating for service account
            state.setText(" Connected ✔️")
            self.state.setStyleSheet("color: green")
            self.auth_flag = True
        except:
            self.auth_flag = False
            state.setText(" Disconnected ❌")
            self.state.setStyleSheet("color: red")
    
        self.data = {
            'setV':[1] * 10,
            'curV':[1] * 10,
            'Ctotal':[.1] * 10,
            'demand':[0] * 10,
            'shift':[[0 for _ in range(3)] for _ in range(10)]
        }
                
    @QtCore.pyqtSlot(dict)
    def on_upload_signal(self,data):
        self.data = data
        self.upload_data()

    def upload_data(self):

        if self.auth_flag:
            try:
                state = self.dm.upload_rex(self.sheet,self.data)
                if state:
                    self.state.setText(" Connected ✔️")
                    self.state.setStyleSheet("color: green")
                    #print("authenticated and uploaded")
                else:
                    self.state.setText(" Disconnected ❌")
                    self.state.setStyleSheet("color: red")
                    #print("authenticated but upload failed")
            except:
                #print("authenticated but internal problem::exc block")
                self.state.setText(" Disconnected ❌")
                self.state.setStyleSheet("color: red")
                
        else:
            try:
                self.sheet = self.dm.auth_access()
                self.state.setText(" Connected ✔️")
                self.state.setStyleSheet("color: green")
                #print("authenticated after sometime ")
            except:
                self.state.setText(" Disconnected ❌")
                self.state.setStyleSheet("color: red")
                #print("not authenticated ")
            

if __name__ == "__main__":
    app = QApplication(sys.argv)

    splash = SplashScreen('resources/flowLogo.png')
    splash.show()

    # Allow UI to update by processing events
    def update_status_with_delay(status, delay=.1):
        splash.show_status(status)
        QtCore.QCoreApplication.processEvents()  # Allow the event loop to update the splash screen
        time.sleep(delay)

    # Status updates
    update_status_with_delay('Initializing Containers.')
    update_status_with_delay('Initializing Containers..')
    update_status_with_delay('Initializing Containers...')

    # Global variables
    shift = -1 
    graph_hour = np.zeros((24, 10), dtype=np.int32)
    active = np.zeros(10, dtype=bool)
    #active_an = np.zeros(10, dtype=bool)
    calib_reg = np.ones(10, dtype=np.int16)
    lakh = 100000 # this is used to control lakh litre value

    update_status_with_delay('Detecting COM ports.')
    update_status_with_delay('Detecting COM ports..')

    # Detect COM port
    ports = serial.tools.list_ports.comports()
    com=''
    for port in ports:
        if port.hwid.find('VID:PID=0403:6001') != -1:
            com = port.device
            break
    
    if not com:
        com = input('Enter the Serial Port name \'eg: COM3\'\n:')

    update_status_with_delay('Detecting COM ports...')

    update_status_with_delay(f'Detected COM port {com}', delay=1)
    update_status_with_delay('Initializing Communication.')
    update_status_with_delay('Initializing Communication..')
    update_status_with_delay('Initializing Communication...')

    # Initialize Communication
    try:
        client = mb(port=com, baudrate=19200, stopbits=1, timeout=.1,retries=2)
        if client.connect:
            update_status_with_delay(f'Communication Initialized!')
        else:
            update_status_with_delay('Initialization Failed',delay=3)
            exit()
    
        
        update_status_with_delay('Detecting Active Meters.')
        update_status_with_delay('Detecting Active Meters..')
        update_status_with_delay('Detecting Active Meters...')

        # Detect active slaves
        for slave_id in range(10):
            response = client.read_holding_registers(address=0, count=1, slave=slave_id + 1)
            #res = client.read_holding_registers(address=0, count=1, slave=slave_id + 1)
            if not response.isError():
                active[slave_id] = True
                update_status_with_delay(f'Meter {slave_id+1} is active')
            # if not res.isError():
                #active_an[slave_id] = True
            #     pass
        client.close()

        update_status_with_delay('Starting...')
        print(f"Connected via serial port :{com}")
    except:
        exit()

    main_app = MainApp()
    splash.finish(main_app)
    main_app.show()

    sys.exit(app.exec_())
    
