#from asyncio.windows_events import NONE
import os
import sys
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QCheckBox, QGridLayout, QHeaderView
from PyQt5.QtCore import pyqtSlot
from pyqtlet import L, MapWidget
from DatabaseSys.Databasesupport import *
from TabbedDialog.tableWithSignalSlot import *
from CustomTool.UI import *

class SiteWidget(QWidget):
    def __init__(self):
        super(SiteWidget,self).__init__()
        self.init_ui()

    def init_ui(self):
        self.setGeometry(QtCore.QRect(10,20,700,700))
        self.setFont(QtGui.QFont("Calibri",10))
        self.faqtree = QtWidgets.QTreeWidget(self)   
        self.faqtree.setHeaderLabel('FAQ')     
        self.faqtree.setGeometry(500,200, 400, 400)
        self.faqtree.setUniformRowHeights(False)
        self.faqtree.setWordWrap(True)
       #self.faqtree.setFont(QtGui.QFont("Calibri",10))        
        self.importfaq("Site")              
        self.faqtree.header().setStretchLastSection(False)  
        self.faqtree.header().setSectionResizeMode(QHeaderView.ResizeToContents)  
        self.faqtree.setVisible(False)

        self.tab_summary = QTextEdit("")        
        self.tab_summary.setPlainText("Here we identify our agriculture SITE (for simulation purposes) with latitude, longitude, altitude and a name. From the LIST box underneath, we can define our SITE or update the existing SITE.") 
        self.tab_summary.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tab_summary.setReadOnly(True)  
        self.tab_summary.setMinimumHeight(10)    
        self.tab_summary.setAlignment(QtCore.Qt.AlignTop)
        # no scroll bars
        self.tab_summary.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.tab_summary.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.tab_summary.setFrameShape(QtWidgets.QFrame.NoFrame)      
        self.helpcheckbox = QCheckBox("Turn FAQ on?")
        self.helpcheckbox.setChecked(False)
        self.helpcheckbox.stateChanged.connect(self.controlfaq)

        urlLink="<a href=\"https://youtu.be/VxEn6QM7nzU/\">Click here \
                to watch the Site Tab video tutorial. </a><br>"
        self.siteVidlabel=QLabel()
        self.siteVidlabel.setOpenExternalLinks(True)
        self.siteVidlabel.setText(urlLink)
       
        self.mainlayout = QGridLayout()
        self.spacer = QSpacerItem(10,10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.vHeader = QVBoxLayout()
        self.vHeader.setContentsMargins(0,0,0,0)
        self.vHeader.addWidget(self.tab_summary)
        self.vHeader.addWidget(self.siteVidlabel)
        self.vHeader.addWidget(self.helpcheckbox)
        self.vHeader.setAlignment(QtCore.Qt.AlignTop)

        ## Setting up the form elements    
        self.sitelabel = QLabel("Site")
        self.sitecombo = QComboBox()
        self.sitelabel.setBuddy(self.sitecombo)
        self.sitelists = read_sitedetailsDB()
        # this way we don't need this entry in database and it is always on the top of the combo
        self.sitecombo.addItem("Select from list") 
        self.sitecombo.addItem("Add New Site") 
        for item in self.sitelists: 
            if item != "Generic Site":
                self.sitecombo.addItem(item)
        self.sitecombo.currentIndexChanged.connect(self.showsitedetails)

        # Setting up MapWidget

        self.MapWidget = MapWidget()

        # Setting the map with pyqtlet
        self.map = L.map(self.MapWidget)
        self.marker = None
        self.map.setView([39.8283,-103.8233],5)
        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)
        self.map.clicked.connect(lambda x:self.updateMap(x))

        


        self.rlatlabel = QLabel("Latitude (deg)")
        self.rlatedit = QLineEdit("")
        self.rlatedit.textEdited.connect(self.updateMapFromText)
        self.rlonlabel = QLabel("Longitude (deg)")
        self.rlonedit = QLineEdit("")
        self.rlonedit.textEdited.connect(self.updateMapFromText)
        self.altlabel = QLabel("Altitude (m)")
        self.altedit = QLineEdit("")
        self.sitenamelabel = QLabel("Site Name")
        self.sitenameedit = QLineEdit("")
        self.savebutton = QPushButton("Update")        
        self.deletebutton = QPushButton("Delete")        

        self.mainlayout.addLayout(self.vHeader,0,0,1,4)
        self.mainlayout.addWidget(self.faqtree,0,4,2,1)
        self.mainlayout.addWidget(self.MapWidget,1,0,4,4)     
        self.mainlayout.addWidget(self.sitelabel,6,0)
        self.mainlayout.addWidget(self.sitecombo,6,1)
        self.mainlayout.addWidget(self.rlatlabel,7,0)
        self.mainlayout.addWidget(self.rlatedit,7,1)
        self.mainlayout.addWidget(self.rlonlabel,8,0)
        self.mainlayout.addWidget(self.rlonedit,8,1)
        self.mainlayout.addWidget(self.altlabel,9,0)
        self.mainlayout.addWidget(self.altedit,9,1)
        self.mainlayout.addWidget(self.sitenamelabel,10,0)
        self.mainlayout.addWidget(self.sitenameedit,10,1)
        self.mainlayout.addWidget(self.savebutton,11,2)
        self.mainlayout.addWidget(self.deletebutton,11,3)
        self.MapWidget.setVisible(True)
        self.rlatlabel.setVisible(False)
        self.rlatedit.setVisible(False)
        self.rlonlabel.setVisible(False)
        self.rlonedit.setVisible(False)
        self.altlabel.setVisible(False)
        self.altedit.setVisible(False)
        self.sitenamelabel.setVisible(False)
        self.sitenameedit.setVisible(False)
        self.savebutton.setVisible(False)       
        self.deletebutton.setVisible(False)        
        self.setLayout(self.mainlayout) 
    
    
    def showsitedetails(self,value):
        '''
        Prepare view for SITE related information.
        '''
        self.MapWidget.setVisible(False)
        self.rlatlabel.setVisible(False)
        self.rlatedit.setVisible(False)
        self.rlonlabel.setVisible(False)
        self.rlonedit.setVisible(False)
        self.altlabel.setVisible(False)
        self.altedit.setVisible(False)
        self.sitenamelabel.setVisible(False)
        self.sitenameedit.setVisible(False)
        self.savebutton.setVisible(False)       
        self.deletebutton.setVisible(False)        

        sitename = str(self.sitecombo.currentText())
        if sitename == "Select from list":
            return True

        self.MapWidget.setVisible(True)
        self.rlatlabel.setVisible(True)
        self.rlatedit.setVisible(True)
        self.rlonlabel.setVisible(True)
        self.rlonedit.setVisible(True)
        self.altlabel.setVisible(True)
        self.altedit.setVisible(True)
        self.sitenamelabel.setVisible(True)
        self.sitenameedit.setVisible(True)
        self.savebutton.setVisible(True)       

        if sitename == 'Add New Site':            
            self.rlatedit.setText("")
            self.rlonedit.setText("")
            self.altedit.setText("")
            self.sitenameedit.setText("")
            self.savebutton.setText("SaveAs")       
            self.map.setView([39.8283,-103.8233],5)
            L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)
            self.map.removeLayer(self.marker)
            self.deletebutton.setVisible(False)              
            self.rlatedit.setReadOnly(False)
            self.rlonedit.setReadOnly(False)
        else:
            site_tuple = extract_sitedetails(self.sitecombo.itemText(value))     
            self.rlatedit.setText(str(site_tuple[1]))
            self.rlatedit.setReadOnly(True)
            self.rlonedit.setText(str(site_tuple[2]))
            self.rlonedit.setReadOnly(True)
            self.altedit.setText(str(site_tuple[3]))
            self.sitenameedit.setText(self.sitecombo.itemText(value))             
            # Setting the map with pyqtlet
            self.map.setView([site_tuple[1],site_tuple[2]],5)
            L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)
            if not self.marker:
                self.marker = L.marker([site_tuple[1],site_tuple[2]])
            else:
                self.marker.setLatLng([site_tuple[1],site_tuple[2]])
            self.marker.bindPopup('Latitude: '+"{:.{}f}".format(site_tuple[1],3)+' Longitude: '+"{:.{}f}".format(site_tuple[2],3))
            self.map.addLayer(self.marker)
            self.sitenamelabel.setVisible(False)
            self.sitenameedit.setVisible(False)     

            self.savebutton.setText("Update")

        self.savebutton.clicked.connect(lambda:self.on_savebuttonclick(self.sitenameedit.text()))
        # Only display delete button if the site is NOT being used in any simulation
        if not isSiteOnPastruns(self.sitecombo.itemText(value)) and sitename != 'Add New Site':
            self.deletebutton.setVisible(True)
            self.deletebutton.clicked.connect(lambda:self.on_deletebuttonclick(sitename))
        

    @pyqtSlot()
    def on_savebuttonclick(self,item1):
        '''
        aim: to save the SITE view data to field table
        '''
        newSitename = str(self.sitenameedit.text())
        if self.savebutton.text() == "SaveAs":
            if(newSitename == ""):
                return messageUser("Site Name is empty, please provide a name.")
        
            site_tuple = extract_sitedetails(newSitename)   
            if site_tuple != 0:
                return messageUser("Failed: Site exists. Change SITE name.") 

        altitude = self.altedit.text()
        if altitude == "":
            return messageUser("Altitude is empty, please provide information.")

        if float(altitude) < 0:
            return messageUser("Altitude should be greater or equal to 0.")

        record_tuple=(newSitename,float(self.rlatedit.text()),float(self.rlonedit.text()),float(self.altedit.text()))
        self.savebutton.disconnect()

        c1 = insert_update_sitedetails(record_tuple,self.savebutton.text())
        if c1:
            self.sitecombo.clear()
            self.sitelists = read_sitedetailsDB() 
            self.sitecombo.addItem("Select from list") 
            self.sitecombo.addItem("Add New Site") 
            for item in self.sitelists:            
                self.sitecombo.addItem(item)


    def importfaq(self, thetabname=None):        
        faqlist = read_FaqDB(thetabname,'') 
        faqcount=0
        
        for item in faqlist:
            roottreeitem = QTreeWidgetItem(self.faqtree)
            roottreeitem.setText(0,item[2])
            childtreeitem = QTreeWidgetItem()
            childtreeitem.setText(0,item[3])
            roottreeitem.addChild(childtreeitem)


    @pyqtSlot()
    def on_deletebuttonclick(self,sitename):
        '''
        aim: delete the SITE data in field table
        '''
        delete_flag = messageUserDelete("Are you sure you want to delete this site?")
        if delete_flag:
            # If any soil is associated with this site, on soil tables set  site_id=23 (Generic Site)
            c1 = delete_sitedetails(str(sitename))
            self.deletebutton.disconnect()
            if c1:
                self.sitecombo.clear()
                self.sitelists = read_sitedetailsDB() #read_fieldDB()
                # this way we don't need this entry in database and it is always on the top of the combo                
                self.sitecombo.addItem("Select from list") 
                self.sitecombo.addItem("Add New Site") 
                for item in self.sitelists:            
                    if item != "Generic Site":
                        self.sitecombo.addItem(item)
            return True
        return False


    @pyqtSlot()
    def updateMap(self,mapInfo):
        if str(self.sitecombo.currentText()) == 'Add New Site':
            lat = mapInfo['latlng']['lat']
            lng = mapInfo['latlng']['lng']
            # Setting the map with pyqtlet
            self.map.setView([lat,lng])
            L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)
            if not self.marker:
                self.marker = L.marker([lat,lng])
            else:
                self.marker.setLatLng([lat,lng])
            self.marker.bindPopup('Latitude: '+"{:.{}f}".format(lat,3)+' Longitude: '+"{:.{}f}".format(lng,3))
            self.map.addLayer(self.marker)
            self.rlatedit.setText("{:.{}f}".format(lat,4))
            self.rlonedit.setText("{:.{}f}".format(lng,4))
            return True


    @pyqtSlot()
    def updateMapFromText(self):
        if str(self.sitecombo.currentText()) == 'Add New Site':
            lat = self.rlatedit.text()
            lng = self.rlonedit.text()
            # Setting the map with pyqtlet
            self.map.setView([lat,lng],5)
            L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)
            if not self.marker:
                self.marker = L.marker([lat,lng])
            else:
                self.marker.setLatLng([lat,lng])
            self.marker.bindPopup('Latitude: '+lat+' Longitude: '+lng)
            self.map.addLayer(self.marker)
            return True


    def controlfaq(self):                
        if self.helpcheckbox.isChecked():
            self.faqtree.setVisible(True)
        else:
            self.faqtree.setVisible(False)

        
    def resource_path(self,relative_path):
        """
        Get absolute path to resource, works for dev and for PyInstaller 
        """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)          

