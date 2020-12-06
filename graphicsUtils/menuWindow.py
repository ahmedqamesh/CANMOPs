from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
from PyQt5.QtWidgets import *
from graphicsUtils import mainWindow


class MenuBar(QWidget):  
    
    def __init__(self, parent=mainWindow):
        super(MenuBar, self).__init__(parent)
        self.MainWindow = mainWindow.MainWindow()

    def stop(self):
        return self.MainWindow.stop_server()
           
    def create_menuBar(self, mainwindow):
        menuBar = mainwindow.menuBar()
        menuBar.setNativeMenuBar(False)  # only for MacOS
        self._fileMenu(menuBar, mainwindow)
        self._interfaceMenu(menuBar, mainwindow)
        self._helpMenu(menuBar, mainwindow)
    # 1. File menu
    def _fileMenu(self, menuBar, mainwindow):
               
        fileMenu = menuBar.addMenu('&File')
        exit_action = QAction(QIcon('graphicsUtils/icons/icon_exit.png'), '&Exit', mainwindow)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit program')
        # exit_action.triggered.connect(self.stop)
        exit_action.triggered.connect(qApp.quit)


        fileMenu.addAction(exit_action)
           
    # 4. Help menu
    def _helpMenu(self, menuBar, mainwindow):
        helpmenu = menuBar.addMenu("&Help")

        about_action = QAction('&About', mainwindow)
        about_action.setStatusTip("About")
        about_action.triggered.connect(self.about)
        helpmenu.addAction(about_action)
        
    # 5. Interface menu
    def _interfaceMenu(self, menuBar, mainwindow):
        interfaceMenu = menuBar.addMenu("&Interface")
        SocketMenu = interfaceMenu.addMenu("&SocketCAN")
        KvaserMenu = interfaceMenu.addMenu("&Kvaser")
        AnagateMenu = interfaceMenu.addMenu("&AnaGate")
        
        RestartSocketcan = QAction(QIcon('graphics_Utils/icons/icon_reset.png'),'Restart SocketCAN channel', mainwindow)
        RestartSocketcan.setStatusTip("Restart SocketCAN")
        RestartSocketcan.triggered.connect( self.MainWindow.restart_socketchannel)
        
        SocketMenu.addAction(RestartSocketcan)
        
        def _dump_can0():
            self.MainWindow.dump_socketchannel(can0.text())

        def _dump_can1():
            self.MainWindow.dump_socketchannel(can1.text())
            
        DumpSocketcan = SocketMenu.addMenu('Dump SocketCAN')
        
        can0 = QAction('can0', mainwindow)
        can0.setStatusTip("can0")
        can0.triggered.connect(_dump_can0)
        
        can1 = QAction('can1', mainwindow)
        can1.setStatusTip("can1")
        can1.triggered.connect(_dump_can1)
                
        DumpSocketcan.addAction(can0)
        DumpSocketcan.addAction(can1)
        
        
    def create_statusBar(self, mainwindow, msg="Ready"):
        status = QStatusBar()
        status.showMessage(msg)
        mainwindow.setStatusBar(status)
        
    def about(self):
        QMessageBox.about(self, "About",
        """CANMoPS is a graphical user interface GUI to read the channels of MOPS chip. The package can communicate with a CAN interface and talks CANopen with the connected Controllers. Currently only CAN interfaces from AnaGate (Ethernet) and Kvaser (USB) are supported.""")
 
        
if __name__ == "__main__":
    pass
                
