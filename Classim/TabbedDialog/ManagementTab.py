from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QTreeWidgetItem, QTextEdit, QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QGridLayout, QCheckBox
from CustomTool.custom1 import *
from CustomTool.UI import *
from DatabaseSys.Databasesupport import *
from Models.cropdata import *
from TabbedDialog.tableWithSignalSlot import *
from CustomTool.createManRepWindow import *

class ManagementTab_Widget(QWidget):
    def __init__(self):
        super(ManagementTab_Widget,self).__init__()
        self.init_ui()


    def init_ui(self):
        self.setGeometry(QtCore.QRect(10,20,700,700))
        self.setFont(QtGui.QFont("Calibri",10))
        self.faqtree = QtWidgets.QTreeWidget(self)   
        self.faqtree.setHeaderLabel('FAQ')     
        self.faqtree.setGeometry(500,200, 400, 400)
        self.faqtree.setUniformRowHeights(False)
        self.faqtree.setWordWrap(True)
      # self.faqtree.setFont(QtGui.QFont("Calibri",10))        
        self.importfaq("management")              
        self.faqtree.header().setStretchLastSection(False)  
        self.faqtree.header().setSectionResizeMode(QHeaderView.ResizeToContents)  
        self.faqtree.setVisible(False)

        self.mainlayout1 = QGridLayout()          
        self.vl1 = QVBoxLayout()    
        
        header5 = ["Crop(s)/Experiment(s)/ Treatment(s)/Operation(s)"]  
        self.tab_summary = QTextEdit("Crop management is a 4 step process and is implemented in a panel below. This \
panel occasionally opens up another panel on its right side to collect supplement but necessary inputs. Process begins \
by A).Clicking the CROP to be managed, B). ADD NEW Experiment by giving it a broader categorical name like `Summer2018`. \
C). Experiment is further defined by ADD NEW Treatment plan by giving it treatment specific name. Note EXPERIMENT can \
have multiple treatments plans like `With Fertilizer`, `Without Fertilizer`. D). Defining the treatment individual \
OPERATION(S) by listing operation, date of operation, operation specific parameters and crop cultivar.<br><b>NOTE</b>: \
If you are modeling multiple treatments that only vary in one management aspect (ex. multiple N levels), use the CopyTo \
button to create copies of the treatment information so you do not need to fill in all of the management data multiple times.")
        self.tab_summary.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tab_summary.setReadOnly(True)   
        
        self.tab_summary.setMaximumHeight(90)    
        self.tab_summary.setAlignment(QtCore.Qt.AlignTop)     
        # no scroll bars
        self.tab_summary.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.tab_summary.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.tab_summary.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # horizontal, vertical
        self.tab_summary.setFrameShape(QtWidgets.QFrame.NoFrame)

        urlLink="<a href=\"https://youtu.be/LoTh4D1zmwI\">Click here \
                to watch the Management Tab Video Tutorial</a><br>"
        self.managementVidlabel=QLabel()
        self.managementVidlabel.setOpenExternalLinks(True)
        self.managementVidlabel.setText(urlLink)

        self.helpcheckbox = QCheckBox("Turn FAQ on?")
        self.helpcheckbox.setChecked(False)
        self.helpcheckbox.stateChanged.connect(self.controlfaq)

        # Creates the management report window
        self.manRepWindow = createManRepWindow()
        # Button to toggle management report window
        self.manRepButton = QPushButton("Open Management Report")
        self.manRepButton.clicked.connect(self.toggleManRepWindow)
        
        # adding loader value. This will control if "Add Experiment/ Add Treatment/ Add Operation" should be added or not
        self.treeWidget = TreeOfTableWidget("crop", "sitedetails", 1, ',', 2, parent=None)

        # View/ViewWidget has drag-drop facilities set here. Model also needs some of the flags checked 
        # in order for this to work.
        self.treeWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.treeWidget.setDragEnabled(True)
        self.treeWidget.viewport().setAcceptDrops(True)
        self.treeWidget.setAcceptDrops(True)
        self.treeWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.treeWidget.setDropIndicatorShown(True)

        self.treeWidget.model().headers = header5
        self.treeWidget.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.treeWidget.header().setStretchLastSection(True)
        
        # hide the treeWidget extra columns
        for column in range(1,self.treeWidget.model().columnCount(QModelIndex())):
            self.treeWidget.setColumnHidden(column,True)
                
        self.test1 = Tabless_Widget()
        self.test1.sitetable1.setVisible(False) 
        ccstatus = self.test1.make_connection_2_tree(self.treeWidget)
        ccstatus2 = self.treeWidget.make_connection_2_table(self.test1)

        if ccstatus:
            self.test1.reset()

        if ccstatus2:
            self.treeWidget.reset()

        self.gl = QGridLayout()
        self.gl.setSpacing(1)
        self.vl1.addWidget(self.tab_summary)  
        self.vl1.addWidget(self.managementVidlabel)
        self.vl1.addWidget(self.helpcheckbox)
        self.vl1.addWidget(self.manRepButton)
        
        self.spacer = QSpacerItem(10,10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.hl1 = QHBoxLayout()
        self.hl1.addWidget(self.treeWidget)
        self.hl1.addWidget(self.test1.sitetable1)
        self.vl1.addLayout(self.hl1)
        self.vl1.addItem(self.spacer)
        self.mainlayout1.addLayout(self.vl1,0,0,10,2)
        self.mainlayout1.addWidget(self.faqtree,0,3)
        self.mainlayout1.setColumnStretch(0,3)
        self.setLayout(self.mainlayout1) 
        self.show()


    def toggleManRepWindow(self):
        if self.manRepWindow.isVisible():
            self.manRepWindow.hide()
        else:
            self.manRepWindow.show()


    def fresh(self):
        self.test1.sitetable1.clear()
        self.test1.sitetable1.reset()
        self.test1.setVisible(False)
        self.test1.sitetable1.hide()


    def make_connection(self,tableWithSignalSlot_object):
        print("$$$$$$$$$$$$ debug coming here in Tab1.py, calling fresh")
        if self.test1.sig2 == 3:
            print("************** debug coming here in Tab1.py, calling fresh")
            tableWithSignalSlot_object.sig2.connect(self.fresh)


    def importfaq(self, thetabname=None):        
        faqlist = read_FaqDB(thetabname,'') 
        for item in faqlist:
            roottreeitem = QTreeWidgetItem(self.faqtree)
            roottreeitem.setText(0,item[2])
            childtreeitem = QTreeWidgetItem()
            childtreeitem.setText(0,item[3])
            roottreeitem.addChild(childtreeitem)


    def controlfaq(self):                
        if self.helpcheckbox.isChecked():
            self.faqtree.setVisible(True)
        else:
            self.faqtree.setVisible(False)