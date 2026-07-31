import os
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QTreeWidgetItem, QTabWidget, QLabel, QHBoxLayout, QVBoxLayout, QHeaderView, QTextBrowser
from PyQt5.QtCore import pyqtSignal
from CustomTool.custom1 import *
from CustomTool.UI import *
from DatabaseSys.Databasesupport import *
from Models.cropdata import *
from TabbedDialog.tableWithSignalSlot import *
from collections import deque
from pathlib import PosixPath

'''
Contains 1 class
1). Class Welcome_Widget is derived from Qwidget. It is initialed and called by Tabs.py -> class Tabs_Widget. It is acting like a index page of a book. It handles all the features of WELCOME Tab on the interface.
    It has signal slot mechanism. It does interact with the DatabaseSys\Databasesupport.py for all the databases related task.
    Pretty generic and self explanotory methods. 
    Refer baseline classes at http://pyqt.sourceforge.net/Docs/PyQt5/QtWidgets.html#PyQt5-QtWidgets
    
    Some of the GLOBALS defined above can be removed sequential after testing. 
    Check out the logic for images/icons.
'''

class About_Widget(QTabWidget):
    # Add a signal to notify parent tab that user has selected following tabindex#     
    welcomesig = pyqtSignal(int)

    def __init__(self):
        super(About_Widget,self).__init__()
        self.init_ui()


    def init_ui(self):
        self.setGeometry(QtCore.QRect(10,20,700,700))
        self.setFont(QtGui.QFont("Calibri",10))
        self.faqtree = QtWidgets.QTreeWidget(self) 
        
        self.mainlayout = QHBoxLayout()  
        self.aboutlayout = QVBoxLayout()  
        self.aboutlayout.setAlignment(QtCore.Qt.AlignTop)
        self.aboutlayout.setContentsMargins(2,2,2,2)  

        # Read crop.db user version
        conn, c = openDB('crop.db')
        query = "pragma user_version"
        cropDB = pd.read_sql_query(query,conn)
        
        # Read cropOutput.db user version
        conn, c = openDB('cropOutput.db')
        query = "pragma user_version"
        cropOutDB = pd.read_sql_query(query,conn)

        # Get Classim version information
        verInfo = getClassimVersion()

        self.summary = '''
<p>CLASSIM Version ''' + str(verInfo) + '''</p>
<p><u>Database</u><br>crop.db version: ''' + str(cropDB['user_version'][0]) + '''<br>cropOutput.db version: ''' + str(cropOutDB['user_version'][0]) + '''</p>
<p>If you have any suggestions or questions, please email ARS-CLASSIM-Help@usda.gov.</p>
<p><b>Development Team<b></p>
<u>Models</u>
<ul>
    <li>2DSoil: Dennis Timlin, Zhuangji Wang and David Fleisher</li>
    <li>Glycim: Wenguang Sun, Vangimalla Reddy and Dennis Timlin</li>
    <li>Gossym: Sahila Beegum and Vangimalla Reddy</li>
    <li>Maizsim: Dennis Timlin and Soo-hyung Kim</li>
    <li>Spudsim: David Fleisher</li>
</ul>
<u>Programmers</u>
<p>Maura Tokay, Alakananda Mitra, Sushil Milak, David Fleisher and Dennis Timlin.</p>
<u>Design & Testing</u>
<p>Maura Tokay, Alakananda Mitra, Sushil Milak, David Fleisher, Dennis Timlin, Vangimalla Reddy, Kirsten Paff, Eunjin Han, Sahila Beegum, Zhuangji Wang and Wenguang Sun.</p>

'''
        self.tab_summary = QTextEdit(self.summary)
        self.tab_summary.setReadOnly(True) 
        self.tab_summary.setMinimumHeight(350)
        # no scroll barsAlign
        self.tab_summary.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.tab_summary.setFrameShape(QtWidgets.QFrame.NoFrame)

        self.aboutlayout.addWidget(self.tab_summary)

        self.ACSLlink = QTextBrowser()
        self.ACSLlink.setOpenExternalLinks(True)
        self.ACSLlink.setHtml('Developed by <a href="https://www.ars.usda.gov/northeast-area/beltsville-md-barc/beltsville-agricultural-research-center/adaptive-cropping-systems-laboratory/">USDA ARS Adaptive Cropping Systems Laboratory</a><br>')

        self.aboutlayout.addWidget(self.tab_summary)
        self.aboutlayout.addWidget(self.ACSLlink)

        self.mainlayout.addLayout(self.aboutlayout)
        self.setLayout(self.mainlayout) 