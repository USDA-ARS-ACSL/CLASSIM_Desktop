__all__ = ["DateAxisItem"]   
from PyQt5 import QtCore
from PyQt5.QtWidgets import QTabBar, QTabWidget, QHBoxLayout
from PyQt5.QtCore import *
from PyQt5.QtGui import QColor
from CustomTool.custom1 import *
from DatabaseSys.Databasesupport import *
from TabbedDialog.ManagementTab import *
from TabbedDialog.tableWithSignalSlot import *
from TabbedDialog.SeasonalTab import *
from TabbedDialog.RotationTab import *
from TabbedDialog.SoilTab import *
from TabbedDialog.WeatherTab import *
from TabbedDialog.CultivarTab import *
from TabbedDialog.RotOutputTab import *
from TabbedDialog.OutputTab import *
from TabbedDialog.WelcomeTab import *
from TabbedDialog.SiteTab import *
from TabbedDialog.AboutTab import *
from TabbedDialog.ExpertSysTab import *

import os


'''
This is main tab for the interface. classim.py (application main entry point) call this tab class.  All the other tabs (Welcome, 
Site, Soil, Cultivar, Weather, Management, Rotation, Output) are attached as sub-tabs to it.

Important: These subtabs are/ and can be linked to each other via "make_connection" method. Take a look.. Useful for 
creating interaction among sub-tabs..PyPl

'''

# for DPI scaling
if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
 
if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] ="1.25"
os.environ["QT_DEVICE_PIXEL_RATIO"] = "auto"



class TabBar(QTabBar):
    def __init__(self, parent):
        QTabBar.__init__(self, parent)


    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        for index in range(self.count()):
            option = QtWidgets.QStyleOptionTab()
            self.initStyleOption(option, index)

            if index == self.currentIndex():
                palette = self.palette()
                palette.setColor(palette.Button, QColor(151,180,152))
                palette.setColor(palette.ButtonText, Qt.black)
                option.palette = palette
            self.style().drawControl(QtWidgets.QStyle.CE_TabBarTab, option, qp, self)
            self.style().drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, option, qp, self)


class Tabs_Widget(QTabWidget):
    def __init__(self):
        super(Tabs_Widget,self).__init__()
        self.setTabBar(TabBar(self))
        self.init_ui()

    def init_ui(self):
        QtWidgets.QMainWindow().setMinimumSize(QtCore.QSize(1000,800))
        font = QtWidgets.QMainWindow().font()
        QtWidgets.QMainWindow().setFont(font)
        self.setFont(font)

        self.Welcometab = Welcome_Widget()
        self.sitetab = SiteWidget()        
        self.soiltab = Soil_Widget()
        self.WeatherTab = Weather_Widget()
        self.Cultivartab = Cultivar_Widget()
        self.Managementtab = ManagementTab_Widget()
        self.Seasonaltab = Seasonal_Widget()
        self.Rotationtab = Rotation_Widget()
        self.Outputtab = Output2_Widget()
        self.RotOutputtab = RotOutput_Widget()
        self.ExpertSysTab = ExpertSys_Widget()
        self.Abouttab = About_Widget()
                
        self.Managementtab.setUpdatesEnabled(True)
        self.addTab(self.Welcometab, ("  Welcome  "))        
        self.addTab(self.sitetab, "  Site  ")                
        self.addTab(self.soiltab, "  Soil  ")        
        self.addTab(self.WeatherTab, "  Weather ")
        self.addTab(self.Cultivartab,"  Cultivar  ")             
        self.addTab(self.Managementtab, ("  Management  ")   )        
        self.addTab(self.Seasonaltab, "  Seasonal Run  ")      
        self.addTab(self.Rotationtab, "  Rotation Builder  ")      
        self.addTab(self.Outputtab, "  Seasonal Output  ")
        self.addTab(self.RotOutputtab, "  Rotation Output  ")
        self.addTab(self.ExpertSysTab, "Expert System")
        self.addTab(self.Abouttab, "  About  ")      

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(9)
        sizePolicy.setVerticalStretch(10)
        self.setSizePolicy(sizePolicy)
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        self.setWindowTitle("CLASSIM - Crop, Land And Soil SIMulation")
      
        # Connecting RotOutput tab with Rotation tab
        self.RotOutputtab.make_connection(self.Rotationtab)

        try:
            self.Seasonaltab.seasonalResetSig.connect(self.ExpertSysTab.reset)
         #   print("Tabs: connected Seasonaltab.seasonalResetSig -> ExpertSysTab.reset")
            self.Seasonaltab.seasonalResetNitroSig.connect(self.ExpertSysTab.reset_nitro)
          #  print("Tabs: connected Seasonaltab.seasonalResetNitroSig -> ExpertSysTab.reset")
        except Exception:
            pass

        self.make_connection(self.Welcometab)     
        self.show()
        self.currentChanged.connect(self.OncurrentChanged)

    def make_connection(self,welcome_object):
        welcome_object.welcomesig.connect(self.OnTabChanged)


    def OnTabChanged(self,MyCurrentTab):
        if 1<= MyCurrentTab <=11:
            print(MyCurrentTab)
            self.setCurrentIndex(MyCurrentTab)
        else:
            self.setCurrentIndex(0)

    def OncurrentChanged(self,MyCurrentTab):
        if self.currentIndex() == 5:
            self.WeatherTab.refresh()
        if self.currentIndex() == 6:
            self.soiltab.reset_view()
        if self.currentIndex() == 7:
            self.Managementtab.fresh()
        if self.currentIndex() == 8:
            self.Seasonaltab.refresh()
        if self.currentIndex() == 9:
            self.Rotationtab.refresh()
        if self.currentIndex() == 11:
            self.ExpertSysTab.reset()

    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)