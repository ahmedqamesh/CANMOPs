########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 01.05.2020
"""
########################################################

from matplotlib.backends.qt_compat import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvas
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
from PyQt5.QtWidgets import *
from PyQt5 import QtGui
import numpy as np
import os
import time
import csv
from csv                    import writer
import binascii
import yaml
import logging
import sys
#try:
from canmopsGUI          import menu_window, mops_child_window,data_monitoring
from canmops.analysis       import Analysis
from canmops.logger_main    import Logger 
from canmops.analysis_utils  import AnalysisUtils
from canmops.can_wrapper_main     import CanWrapper
    #from canmops.mops_readout_thread import READMops
#except:
#    pass
log_call = Logger(name = "MOPS-HUB  GUI ",console_loglevel=logging.INFO, logger_file = False)

rootdir = os.path.dirname(os.path.abspath(__file__)) 
lib_dir = rootdir[:-11]
config_dir = "config_files/"
config_yaml =config_dir + "mops_config.yml"
icon_location = "canmopsGUI/icons/"
class mopshubWindow(QWidget): 

    def __init__(self, console_loglevel=logging.INFO):
       super(mopshubWindow, self).__init__(None)
       self.logger = log_call.setup_main_logger()
       #self.MenuBar = menu_window.MenuWindow(self)
       self.MOPSChildWindow = mops_child_window.MopsChildWindow(self, opcua_config="opcua_config.yaml")
       self.DataMonitoring = data_monitoring.DataMonitoring(self)
       self.update_opcua_config_box()
       # get Default info 
       self.__bus_num = 2
       self.__mops_num = 4

    def update_opcua_config_box(self):
        self.conf_cic = AnalysisUtils().open_yaml_file(file=config_dir + "mopshub_config.yaml", directory=lib_dir)
        self.__CrateID = self.conf_cic["Crate ID"]
        self.__cic_num = len(self.conf_cic["MOPSHUB"])
        
    def Ui_ApplicationWindow(self,mainWindow):
        self.mainWindow = mainWindow
        self.mopshubWindow = QMainWindow()
        
        self.mopshub_window(childWindow=self.mopshubWindow)
        #self.adjustSize()
        self.mopshubWindow.show()
        # dummy way of producing a fake opcua
        self.initiate_mopshub_timer()
        
    def update_device_box(self):
        '''
        The function Will update the configured device section with the registered devices according to the file main_cfg.yml
        '''
        conf = AnalysisUtils().open_yaml_file(file=config_yaml, directory=lib_dir)
        mops_child = mops_child_window.MopsChildWindow()
        deviceName, version, icon_dir,nodeIds, self.__dictionary_items, self.__adc_channels_reg,\
        self.__adc_index, self.__chipId, self.__index_items, self.__conf_index, self.__mon_index, self.__resistor_ratio, self.__ref_voltage   = mops_child.configure_devices(conf)       
    
    def initiate_adc_timer(self, period=None,cic=None, mops=None, port=None):
        '''
        The function will  update the GUI with the ADC data ach period in ms.
        '''  
        _default_file = "mopshub_data_"+cic+"_"+port+"_"+mops+".csv"
        self.logger.notice("Preparing an output file [%s]..." % (lib_dir + "/output_data/"+_default_file))
        self.out_file_csv[int(cic)][int(port)][int(mops)] = AnalysisUtils().open_csv_file(outname=_default_file[:-4], directory=lib_dir + "/output_data") 
            
        # Write header to the data
        fieldnames = ['Time', 'Channel', "nodeId", "ADCChannel", "ADCData" , "ADCDataConverted"]
        self.csv_writer = csv.DictWriter(self.out_file_csv[int(cic)][int(port)][int(mops)], fieldnames=fieldnames)
        self.csv_writer.writeheader()   
            
        self.ADCDummytimer[int(cic)][int(port)][int(mops)] = QtCore.QTimer(self)
        msg = "CIC " + str(cic)+ ", MOPS: " + str(mops)+ ", Port " + str(port)
        self.logger.notice("Reading ADC data [%s]"%msg)
        self.ADCDummytimer[int(cic)][int(port)][int(mops)].setInterval(period)
        self.ADCDummytimer[int(cic)][int(port)][int(mops)].timeout.connect(lambda: self.update_mopshub_adc_channels(int(cic),int(port),int(mops)))
        self.ADCDummytimer[int(cic)][int(port)][int(mops)].start()

    def update_mopshub_adc_channels(self,c,b,m):
        #gc.collect() 
        _dictionary = self.__dictionary_items
        _adc_indices = list(self.__adc_index)
        _adc_channels_reg = self.mainWindow.get_adc_channels_reg()
        self.csv_writer = csv.writer(self.out_file_csv[c][b][m])
        #data_point = [0] * 33
        for i in np.arange(len(_adc_indices)):
            _subIndexItems = list(AnalysisUtils().get_subindex_yaml(dictionary=_dictionary, index=_adc_indices[i], subindex="subindex_items"))
            self.mainWindow.set_index(_adc_indices[i]) 
            #adc_converted = []
            _start_a = 3  # to ignore the first subindex it is not ADC
            for subindex in np.arange(_start_a, len(_subIndexItems) + _start_a - 1):
                s = subindex - _start_a
                s_correction = subindex - 2
                self.mainWindow.set_subIndex(_subIndexItems[s_correction])
                # read SDO UHAL messages
                #data_point, reqmsg, requestreg, respmsg,responsereg , status = self.read_sdo_uhal(c,b,m) #np.random.randint(0,100)     
                data_point =  self.mainWindow.read_sdo_can()  # _thread(print_sdo=False) #
                reqmsg, requestreg, respmsg,responsereg , status = None, None,None,None
                #data_point = "(c%s|b%s|m%s|s%s)"%(c,b,m,s)   
                ts = time.time()
                adc_converted = None
                if data_point is not None: 
                    adc_converted = Analysis().adc_conversion(_adc_channels_reg[str(subindex)], 
                                                                               data_point, 
                                                                               int(self.__resistor_ratio),
                                                                               int(self.__ref_voltage))                   
                    self.channelValueBox[c][b][m][s].setText(str(round(adc_converted, 3)))   
                    #self.status_x, self.status_y = self.DataMonitoring.update_communication_status(req =int(reqmsg),res =int(respmsg), graphWidget = self.statusGraphWidget)
                    #if len(self.status_x)>= 20: self.DataMonitoring.reset_status_data_holder(req =int(reqmsg),res =int(respmsg),graphWidget = self.statusGraphWidget) 
                    if self.trendingBox[c][b][m][s] == True:
                        if len(self.x[s]) >= 20:# Monitor a window of 100 points is enough to avoid Memory issues 
                            self.DataMonitoring.reset_data_holder(adc_converted,s) 
                        self.DataMonitoring.update_figure(data=adc_converted, subindex=subindex, graphWidget = self.graphWidget[s])
                    #This will be used later for limits 
                    if adc_converted >=1.5:
                        self.update_alarm_limits(high=True, low=None, normal=None, object=self.channelValueBox[c][b][m][s]) 
                        self.update_alarm_status(on=False, off=True, warning=False, button=self.mops_alarm_led[c][b][m],button_type = "Movie")
                    elif (adc_converted >=0.025 and adc_converted <=0.1):
                        self.update_alarm_limits(high=None, low=True, normal=None, object=self.channelValueBox[c][b][m][s])
                        self.update_alarm_status(on=False, off=False, warning=True, button=self.mops_alarm_led[c][b][m],button_type = "Movie")
                    else:
                        self.channelValueBox[c][b][m][s].setStyleSheet("color: black;")
                        self.update_alarm_status(on=True, off=False, warning=False, button=self.mops_alarm_led[c][b][m],button_type = "Movie")               
                else: self.channelValueBox[c][b][m][s].setText(str(adc_converted))
                elapsedtime = ts - self.__mon_time
                self.csv_writer.writerow((str(elapsedtime),
                                     str(1),
                                     str(b),
                                     str(self.get_nodeId(c, b, m)),
                                     str(str(subindex)),
                                     str(_adc_indices[i]),
                                     str(_subIndexItems[s_correction]),
                                     str(data_point),
                                     str(adc_converted),
                                     str(reqmsg),
                                     str(requestreg), 
                                     str(respmsg),
                                     str(responsereg), 
                                     status))                                    
            self.update_mopshub_configuration_values(c,b,m)
            self.update_mopshub_monitoring_values(c,b,m)
            
    def update_mopshub_configuration_values(self,c,b,m):
        '''
        The function will will send a CAN message to read configuration values using the function read_sdo_can and 
         update the confValueBox in configuration_values_window.
        The calling function is initiate_adc_timer.
        ''' 
        _dictionary = self.__dictionary_items
        _conf_indices = list(self.__conf_index)                     
        a = 0 
        for i in np.arange(len(_conf_indices)):
            _subIndexItems = list(AnalysisUtils().get_subindex_yaml(dictionary=_dictionary, index=_conf_indices[i], subindex="subindex_items"))
            self.set_index(_conf_indices[i])  # set index for later usage
            for s in np.arange(0, len(_subIndexItems)):
                self.set_subIndex(_subIndexItems[s])
                conf_adc_value , _, _, _,_ , _ = self.read_sdo_uhal(c,b,m) #np.random.randint(0,100)
                #conf_adc_value= np.random.randint(0,100) #
                self.confValueBox[c][b][m][a].setText(str(conf_adc_value))      
                a = a + 1    
                #time.sleep(self.__timeout)

    def update_mopshub_monitoring_values(self,c,b,m):
        '''
        The function will will send a CAN message to read monitoring values using the function read_sdo_can and
         update the monValueBox in monitoring_values_window.
        The calling function is initiate_adc_timer.
        ''' 
        _dictionary = self.__dictionary_items                
        _mon_indices = list(self.__mon_index)    
        a = 0
        for i in np.arange(len(_mon_indices)):
            self.set_index(_mon_indices[i])  # set index for later usage
            _subIndexItems = list(AnalysisUtils().get_subindex_yaml(dictionary=_dictionary, index=_mon_indices[i], subindex="subindex_items"))
            for s in np.arange(0, len(_subIndexItems)):
                self.set_subIndex(_subIndexItems[s])
                mon_adc_value , _, _, _,_ , _ = self.read_sdo_uhal(c,b,m) #
                #mon_adc_value = np.random.randint(0,100)
                self.monValueBox[c][b][m][a].setText(str(mon_adc_value))
                a = a + 1  
                #time.sleep(self.__timeout) 

    def stop_adc_timer(self,cic=None, mops=None, port=None):
        '''
        The function will  stop the adc_timer.
        '''        
        try:
            self.ADCDummytimer[int(cic)][int(port)][int(mops)].stop()
            self.logger.notice("Stopping ADC data reading...")
        except Exception:
            pass
                
    def initiate_mopshub_timer(self, period=1000):
        '''
        The function will  update the GUI with the ADC data ach period in ms.
        '''  
        #self.logger.notice("Reading ADC data...")
        self.__mon_time = time.time() 
        fieldnames = ['Time', 'Channel', "nodeId", "ADCChannel", "ADCData" , "ADCDataConverted"]                
        #cic_file = "mopshub_cic_"+str(c)+"_"+str(b)+".csv"
       # self.logger.notice("Preparing an output file [%s]..." % (lib_dir + "/output_data/"+_cic_file))
       # self.out_file_csv = AnalysisUtils().open_csv_file(outname=_cic_file[:-4], directory=lib_dir + "output_data") 

        #writer = csv.DictWriter(self.out_file_csv, fieldnames=fieldnames)
        #writer.writeheader()  
        self.CicDummytimer = QtCore.QTimer(self)
        self.CicDummytimer.setInterval(period)
        self.CicDummytimer.timeout.connect(lambda: self.set_adc_cic())
        self.CicDummytimer.start()

    def stop_mopshub_timer(self, cic=None, port=None):
        '''
        The function will  stop the adc_timer.
        '''        
        try:
            self.CicDummytimer[int(cic)][int(port)].stop()
            self.logger.notice("Stopping CIC timer...")
        except Exception:
            pass
            
    def mopshub_window(self, childWindow):
        # create MenuBar
        self.MenuBar = menu_window.MenuWindow(childWindow)
        self.MenuBar.create_opcua_menuBar(childWindow,config_yaml)
        
        childWindow.setObjectName("MOPS-HUB Network")
        childWindow.setWindowTitle("MOPS-HUB Network")
        childWindow.setWindowIcon(QtGui.QIcon(icon_location+'icon_nodes.png'))
        childWindow.adjustSize()    
        bus_num = self.__bus_num
        cic_num = self.__cic_num
        mops_num = self.__mops_num
        #frame_width =550 * cic_num/2
        #frame_length =350 * cic_num/2 +200
        #childWindow.setFixedSize(frame_width,frame_length)
        # childWindow.setGeometry(200, 100, 50, 200)
        plotframe = QFrame()  
        childWindow.setCentralWidget(plotframe)
       # childWindow.resize(childWindow.sizeHint().width,childWindow.size().height() + plotframe.sizeHint().height()) 
        logo_layout = QHBoxLayout()
        uni_logo_label = QLabel()
        pixmap = QPixmap(icon_location+'icon_wuppertal_banner.png')
        uni_logo_label.setPixmap(pixmap.scaled(150, 50)) 
        #icon_spacer = QSpacerItem(250, 50, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        interfaceLabel = QLabel()
        interfaceLabel.setText("Crate ID: %s"%str(self.__CrateID))
        
        info_layout = QVBoxLayout()
        cicLabel = QLabel()
        cicLabel.setText("No. Connected CIC: %s"%str(cic_num))
        info_layout.addWidget(interfaceLabel)
        info_layout.addWidget(cicLabel)
        
        
        logo_layout.addLayout(info_layout) 
        logo_layout.addWidget(uni_logo_label)  
        
                    
        mopshubGridLayout = QGridLayout()
        #  Prepare a cic window
        self.ADCDummytimer      = [[[t for t in np.arange(mops_num)]] * bus_num] * cic_num
        self.CicDummytimer      = [[t for t in np.arange(bus_num)]] * cic_num
        self.out_file_csv       = [[[t for t in np.arange(mops_num)]] * bus_num] * cic_num
        self.en_button          = [[k for k in np.arange(bus_num)]] * cic_num
        self.statusBoxVar       = [[k for k in np.arange(bus_num)]] * cic_num
        
        self.bus_alarm_led      = [[k for k in np.arange(bus_num)]] * cic_num
        
        self.Adc_cic_channel    = ["    UH", "    UL", " VCAN", " Temp", "  GND"]
        self.adc_text_box       = [[[ch for ch in self.Adc_cic_channel]] * bus_num] * cic_num
        self.channelValueBox    = [[[ch for ch in np.arange(mops_num)]] * bus_num] * cic_num 
        self.trendingBox        = [[[ch for ch in np.arange(mops_num)]] * bus_num] * cic_num
        self.monValueBox        = [[[ch for ch in np.arange(mops_num)]] * bus_num] * cic_num
        self.confValueBox       = [[[ch for ch in np.arange(mops_num)]] * bus_num] * cic_num
        
        self.mopsBotton         = [[[k  for k  in np.arange(mops_num)]] * bus_num] * cic_num
        self.mops_alarm_led     = [[[m  for m  in np.arange(mops_num)]] * bus_num] * cic_num     
        # Prepare a log window
        self.textOutputWindow()        

        #close button
        buttonLayout = QHBoxLayout() 
        close_button = QPushButton("Close")
        close_button.setIcon(QIcon(icon_location+'icon_close.png'))
        close_button.resize(50, 50)
        close_button.clicked.connect(self.stop_mopshub)
        buttonLayout.addSpacing(cic_num*250)
        buttonLayout.addWidget(close_button)
        
        mopshubGridLayout.addLayout(logo_layout, 0, 0)
        cic_row_len = int(cic_num / 2)
        for c in np.arange(cic_num):
            CICGroupBox = self.def_cic_frame(c)
            if (c) < cic_row_len:
                mopshubGridLayout.addWidget(CICGroupBox, 1, cic_row_len + (c - cic_row_len))
            else:
                mopshubGridLayout.addWidget(CICGroupBox, 2, c - cic_row_len)         
        mopshubGridLayout.addWidget(self.textGroupBox, cic_num + 2, 0, cic_row_len, cic_row_len)
        mopshubGridLayout.addLayout(buttonLayout, cic_num + 4,0, cic_row_len, cic_row_len)
        plotframe.setLayout(mopshubGridLayout)
        self.MenuBar.create_statusBar(childWindow)
        QtCore.QMetaObject.connectSlotsByName(childWindow)

    def stop_mopshub(self):

        self.logger.warning('Stopping the main MOPSHUB window')
        for c in np.arange(self.__cic_num): 
            for b in np.arange(self.__bus_num):
                self.stop_mopshub_timer(cic=c, port=b)
                for m in np.arange(self.__mops_num):
                    self.stop_adc_timer(cic=c, mops=m, port=b)
        sys.exit()
                
    def def_cic_frame(self, c):
        # Define CIC Layout
        bus_num = self.__bus_num
        cic_num = self.__cic_num
        CICGridLayout = QGridLayout()
        CICGroupBox = QGroupBox("        CIC" + str(c))
        CICGroupBox.setStyleSheet("QGroupBox { font-weight: bold;font-size: 16px; background-color: #eeeeec; } ") 
        _ , self.en_button[c], self.bus_alarm_led[c], self.statusBoxVar[c] =  self.def_bus_variables(c,bus_num)
        self.adc_text_box[c]   = self.get_bus_adc_text_box()
        self.mops_alarm_led[c] = self.get_bus_mops_led(c)
        self.mopsBotton[c]     = self.get_bus_mops(c)
        for b in np.arange(bus_num): 
            true_bus_number = self.get_true_bus_number(b, c)
            BusGroupBox = self.def_bus_frame(c, b,true_bus_number)
            CICGridLayout.addWidget(BusGroupBox, 3, b, 1, 1)
        CICGroupBox.setLayout(CICGridLayout)
        return CICGroupBox
    
    def def_bus_frame(self, c, b, true_bus_number): 
        icon = QIcon()
        icon.addPixmap(QPixmap(icon_location+'icon_connect.jpg'), QIcon.Normal, QIcon.On)
        icon.addPixmap(QPixmap(icon_location+'icon_disconnect.jpg'), QIcon.Normal, QIcon.Off)
        BusGridLayout = QGridLayout()  
        StatLayout = QGridLayout()  
        ADCGroupBox = self.def_adc_frame(c,b)
        mopsBottonLayout = self.def_mops_frame(c,b,true_bus_number)
        BusGroupBox = QGroupBox("Port " + str(true_bus_number))
        BusGroupBox.setStyleSheet("QGroupBox { font-weight: bold;font-size: 10px; background-color: #eeeeec; } ")
        
        statusLabelVar = QLabel()
        statusLabelVar.setStyleSheet("QLabel { font-weight: font-size: 8px; background-color:  #eeeeec; } ") 
        statusLabelVar.setText("Bus Status:")   
        itemSpacer = QSpacerItem(50, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)            
        StatLayout.addWidget(statusLabelVar, b, 0)
        StatLayout.addWidget(self.statusBoxVar[c][b] , b, 1)
        StatLayout.addWidget(self.bus_alarm_led[c][b], b, 2)
        StatLayout.addWidget(self.en_button[c][b]    , b, 3)   
        StatLayout.addItem(itemSpacer, b, 4) 
        
        BusGridLayout.addWidget(ADCGroupBox, 0, 0, 1, 2) 
        BusGridLayout.addLayout(StatLayout, 1, 0, 1, 2)
        BusGridLayout.addLayout(mopsBottonLayout, 2, 0, 1, 1)
        BusGroupBox.setLayout(BusGridLayout)
        return BusGroupBox

    
    def def_alert_leds(self, bus_alarm=None, mops_alarm=None, cic=None, mops=None, bus = None, icon_state=False):
        cic_num = self.__cic_num+1
        bus_num = self.__bus_num
        if mops_alarm is True:
            icon_red = icon_location+'icon_disconnected_device.png' #icon_red.gif"
            icon_green = icon_location+'icon_green.gif'
            if icon_state:
                alarm_led = QMovie(icon_green)
            else: 
               alarm_led = QMovie(icon_red)    
            alarm_led.setScaledSize(QSize().scaled(20, 20, Qt.KeepAspectRatio)) 
            alarm_led.start()
            return alarm_led         
        
        if bus_alarm is True:
            icon_red = icon_location+'icon_red.png'
            icon_green = icon_location+'icon_green.png'
            alarm_led = [0] * bus_num
            alarm_led[cic] = QLabel() 
            if icon_state:
                pixmap = QPixmap(icon_green)
            else: 
                pixmap = QPixmap(icon_red)    
            alarm_led[cic].setPixmap(pixmap.scaled(20, 20))            
            return alarm_led[cic] 
    
    
    def def_mops_frame(self, c, b,true_bus_number):
        # # Details for each MOPS
        mops_num = self.__mops_num
        bus_num =self.__bus_num
        icon_mops = icon_location+'icon_mops.png'
        mopsBottonLayout = QGridLayout()
        self.update_device_box()
        for m in np.arange(mops_num):   
            mopsBottonLayout.addWidget(self.mops_alarm_led[c][b][m], m + 3, 0, 1, 1)
            mopsBottonLayout.addWidget(self.mopsBotton[c][b][m], m + 3, 1, 1, 1)
            #mopsBottonLayout.addWidget(mopsBotton[m], m + 3, 1, 1, 1) 
        return mopsBottonLayout
    
    def def_adc_frame(self, c,b):
        self.Adc_cic_channel = ["    UH", "    UL", " VCAN", " Temp", "  GND"]
        Adc_cic_description = ["[ADC ch0]", "[ADC ch1]", "[ADC ch2]", "[ADC ch3]", "[ADC ch4]"]
        adclabels = [ch for ch in self.Adc_cic_channel]
        ADCLayout = QGridLayout()
        ADCGroupBox = QGroupBox("ADC CAN Bus")
        ADCGroupBox.setStyleSheet("QGroupBox { font-weight: bold;font-size: 10px; background-color: #eeeeec; } ")                  
        for ch in np.arange(len(self.Adc_cic_channel)):                
            adclabels[ch] = QLabel()
            adclabels[ch].setStyleSheet("QLabel { font-weight: font-size: 8px; background-color:  #eeeeec; } ") 
            adclabels[ch].setText(self.Adc_cic_channel[ch])
            adclabels[ch].setStatusTip(Adc_cic_description[ch])
            ADCLayout.addWidget(adclabels[ch], 0, ch) 
            ADCLayout.addWidget(self.adc_text_box[c][b][ch], 1, ch)    
        ADCGroupBox.setLayout(ADCLayout)  
        return  ADCGroupBox  
     
    
    def get_bus_mops_led(self,c):
        
        bus_num =self.__bus_num 
        bus_mops_leds =  [[k for k in np.arange(bus_num)]]*self.__mops_num
        for b in np.arange(bus_num):
            bus_mops_leds[b] = self.def_mops_led(b,c)
        return bus_mops_leds
         
    def def_mops_led(self,b,c):
        mops_num = self.__mops_num
        mops_led = [k for k in np.arange(mops_num)]
        for m in np.arange(mops_num):
            mops_led[m] = QLabel()
            status = self.check_mops(c, b, m)
            mops_alarm_led = self.def_alert_leds(mops_alarm=True, cic=c, mops=m, bus = b, icon_state=status)   
            mops_led[m].setMovie(mops_alarm_led)    
        return mops_led 
                 
    def get_bus_mops(self,c):
        bus_num =self.__bus_num 
        bus_mops =  [[k for k in np.arange(bus_num)]]*self.__mops_num
        for b in np.arange(bus_num):
            true_bus_number = self.get_true_bus_number(b, c)
            bus_mops[b] = self.def_mops(b,c,true_bus_number)
        return bus_mops
 
    def def_mops(self,b,c,true_bus_number):
        mops_num = self.__mops_num
        mopsBotton = [k for k in np.arange(mops_num)]
        icon_mops = icon_location+'icon_mops.png'
        for m in np.arange(mops_num):
            status = self.check_mops(c, b, m)
            mopsBotton[m] = QPushButton("  [" + str(m) + "]")
            mopsBotton[m].setObjectName("C" + str(c) + "M" + str(m) + "P" + str(b))
            mopsBotton[m].setIcon(QIcon(icon_mops))
            mopsBotton[m].setStatusTip("CIC NO." + str(c) + " MOPS No." + str(m) + " Port No." + str(true_bus_number))
            mopsBotton[m].clicked.connect(self.get_mops_device)
            if status:        
                pass
            else:
                mopsBotton[m].setEnabled(False)      
        return mopsBotton 
       
    def get_bus_adc_text_box(self): 
        bus_num =self.__bus_num 
        adctextBox =  [[k for k in np.arange(bus_num)]]*len(self.Adc_cic_channel)
        for b in np.arange(bus_num):
            adctextBox[b] = self.def_adc_text_box()
        return adctextBox
    
    def def_adc_text_box(self):
        adctextBox = [k for k in np.arange(len(self.Adc_cic_channel))]
        for ch in np.arange(len(self.Adc_cic_channel)):
            adctextBox[ch] = QLineEdit(str(ch))
            adctextBox[ch].setStyleSheet("background-color: white; border: 1px inset black;")
            adctextBox[ch].setReadOnly(True) 
            adctextBox[ch].setFixedWidth(40)
        return adctextBox                     

    def def_bus_variables(self, cic, bus_num):
        en_button = [k for k in np.arange(bus_num) ]
        statusBoxVar = [k for k in np.arange(bus_num) ]
        bus_alarm_led = [k for k in np.arange(bus_num) ]
        statusLabelVar = [k for k in np.arange(bus_num) ]        
        icon = QIcon()
        icon.addPixmap(QPixmap(icon_location+'icon_connect.jpg'), QIcon.Normal, QIcon.On)
        icon.addPixmap(QPixmap(icon_location+'icon_disconnect.jpg'), QIcon.Normal, QIcon.Off)
        for b in np.arange(bus_num):
            true_bus_number = self.get_true_bus_number(b, cic)
            en_button[b] = QPushButton("")
            en_button[b].setIcon(icon)
            en_button[b].setStatusTip("C" + str(cic) + "_b" + str(true_bus_number))
            en_button[b].setObjectName("C" + str(cic) + "_b" + str(true_bus_number))
            en_button[b].setCheckable(True)
            en_button[b].clicked.connect(lambda: self.set_bus_enable(cic, true_bus_number))

            bus_alarm_led[b] = self.def_alert_leds(bus_alarm=True, cic=b, mops=None, icon_state=False)     
            statusBoxVar[b] = QLineEdit()
            statusBoxVar[b].setStyleSheet("background-color: white; border: 1px inset black;")
            statusBoxVar[b].setReadOnly(True) 
            statusBoxVar[b].setFixedWidth(40)
            statusBoxVar[b].setText("OFF")    
            
            statusLabelVar[b] = QLabel()
            statusLabelVar[b].setStyleSheet("QLabel { font-weight: font-size: 8px; background-color:  #eeeeec; } ") 
            statusLabelVar[b].setText("Bus Status:")               
        return statusLabelVar, en_button, bus_alarm_led, statusBoxVar

            
                             
    def textOutputWindow(self):
        '''
        The function defines the GroupBox output window for the CAN messages
        '''  
        self.textGroupBox = QGroupBox("Log Window")
        self.textBox = QTextEdit()
        self.textBox.setReadOnly(True)
        self.textBox.resize(30, 30)
        textOutputWindowLayout = QGridLayout()
        textOutputWindowLayout.addWidget(self.textBox, 1, 0)
        self.textGroupBox.setLayout(textOutputWindowLayout)
            
    # show windows
    def show_deviceWindow(self, cic=None, mops=None, port=None):
        deviceWindow = QMainWindow(self)
        _device_name = "CIC:" + cic + ", Port:"+port+", MOPS:"+mops
        device_config = "mops"
        adc_channels_num = 33
        self.channelValueBox[int(cic)][int(port)][int(mops)], \
        self.trendingBox[int(cic)][int(port)][int(mops)],\
        self.monValueBox[int(cic)][int(port)][int(mops)] ,\
        self.confValueBox[int(cic)][int(port)][int(mops)], _ = self.MOPSChildWindow.device_child_window(deviceWindow,  
                                                                                                       device=_device_name,
                                                                                                       device_config = device_config,
                                                                                                       cic=cic, 
                                                                                                       mops=mops, 
                                                                                                       port=port, 
                                                                                                       mainWindow = self)
        self.graphWidget = self.DataMonitoring.initiate_trending_figure(n_channels=adc_channels_num)    
        self.initiate_adc_timer(period = 1000, cic=cic, mops=mops, port=port)
        deviceWindow.show()


    # Action windows     
    def set_textBox_message(self, comunication_object=None, msg=None):
        if comunication_object == "SDO_RX": 
            color = QColor("black")
            mode = "RX [hex] :"
        if comunication_object == "SDO_TX": 
            color = QColor("blue") 
            mode = "TX [hex] :"
        if comunication_object == "INFO": 
            color = QColor("green")
            mode = " "
        if comunication_object == "ADC": 
            color = QColor("green")
            mode = " :"
        if comunication_object == "ErrorFrame": 
            color = QColor("red")
            mode = "E:  "
        if comunication_object == "newline":
            color = QColor("green")
            mode = ""        
        self.textBox.setTextColor(color)
        self.textBox.append(mode + msg)
    
    def clear_textBox_message(self):
         self.textBox.clear()
        
    def check_mops(self, c, b, m):
        try:
            port_num = self.conf_cic["MOPSHUB"]["CIC " + str(c)]["Port "+str(b)]["MOPS " + str(m)]["Port"]
            if (port_num == b and self.conf_cic["MOPSHUB"]["CIC " + str(c)]["Port "+str(b)]["MOPS " + str(m)]["Status"]== True):
                status = True
            else:
                status = False
                msg = "CIC " + str(c), "MOPS " + str(m), "Port " + str(b), ": Not Found"
                self.set_textBox_message(comunication_object = "ErrorFrame" , msg = str(msg)) 
        except:
            status = False
        return status
             

    def get_true_bus_number(self, bus_id, cic_id):
        true_bus_number = (33 - (bus_id + 1) - (2 * cic_id))
        return true_bus_number
    
    def get_reverse_bus_number(self, true_bus_number, cic_id):
        bus_id = -1 - (true_bus_number + (2 * cic_id) - 33)
        return str(bus_id)
    
    def set_bus_enable(self, c, b):
        sender = self.sender().objectName()
        _cic_id = sender[1:-4]
        _true_port_id = sender[4:]
        _port_id = self.get_reverse_bus_number(int(_true_port_id), int(_cic_id))
        print(sender, "is clicked")
        en_button_check = self.en_button[int(_cic_id)][int(_port_id)].isChecked()
        if en_button_check:
            print("Checked")
            self.update_bus_status_box(cic_id=_cic_id, port_id=_port_id, on=True)
        else:
            self.update_bus_status_box(cic_id=_cic_id, port_id=_port_id, off=True)

    def set_adc_cic(self):
        # A possibility to save the data into a file
        for c in np.arange(self.__cic_num): 
            for b in np.arange(self.__bus_num):  
                for ch in np.arange(5):
                    ts = time.time()
                    elapsedtime = ts -  self.__mon_time
                    adc_value = np.random.randint(0, 100)
                    self.adc_text_box[c][b][ch].setText(str(adc_value))
                    # This will be used later for limits 
                    if adc_value >= 90:self.update_alarm_limits(high=True, object=self.adc_text_box[c][b][ch]) 
                    if adc_value <= 5 : self.update_alarm_limits(low=True, object=self.adc_text_box[c][b][ch]) 
                    else: self.update_alarm_limits(normal=True, object=self.adc_text_box[c][b][ch])

    def update_alarm_limits(self, high=None, low=None, normal=None, object=None):
        if high:   object.setStyleSheet(" background-color: red;")
        if low :   object.setStyleSheet(" background-color: yellow;")
        if normal: object.setStyleSheet("color: black;")
        else: pass  
                
    def update_bus_status_box(self, cic_id=None, port_id=None, on=False, off=False):
        icon_red = icon_location+'icon_red.png'
        icon_green = icon_location+'icon_green.png' 
        if on:
            pixmap = QPixmap(icon_green)
            self.en_button[int(cic_id)][int(port_id)].setIcon(QIcon(icon_location+'icon_connect.jpg'))    
            self.statusBoxVar[int(cic_id)][int(port_id)].setText("ON")
            self.en_button[int(cic_id)][int(port_id)].setChecked(True)
            self.bus_alarm_led[int(cic_id)][int(port_id)]
        else:
            pixmap = QPixmap(icon_red)
            self.statusBoxVar[int(cic_id)][int(port_id)].setText("OFF")
            self.en_button[int(cic_id)][int(port_id)].setIcon(QIcon(icon_location+'icon_disconnect.jpg'))    
            self.en_button[int(cic_id)][int(port_id)].setChecked(False)
            self.bus_alarm_led[int(cic_id)][int(port_id)]
        self.bus_alarm_led[int(cic_id)][int(port_id)].setPixmap(pixmap.scaled(20, 20))   
            
    def update_alarm_status(self, on=False, off=False, warning=False, button=None, button_type = "Movie"):
     
        if button_type == "Movie":
            icon_red = icon_location+'icon_red_alarm.gif'
            icon_green = icon_location+'icon_green.gif'
            icon_yellow = icon_location+'icon_yellow.gif'  
        
            if on: 
                alarm_led = QMovie(icon_green)
            if off:
               alarm_led = QMovie(icon_red) 
            if warning:
               alarm_led = QMovie(icon_yellow) 
            alarm_led.setScaledSize(QSize().scaled(20, 20, Qt.KeepAspectRatio)) 
            alarm_led.start()
            button.setMovie(alarm_led) 
            
        if button_type == "Label":
            icon_red = icon_location+'icon_red_alarm.png'
            icon_green = icon_location+'icon_green.png'
            icon_yellow = icon_location+'icon_yellow.png'  
            if on: 
                pixmap = QPixmap(icon_green)
            if off:
               pixmap = QPixmap(icon_red)
            if warning:
               pixmap = QPixmap(icon_yellow) 
            button.setPixmap(pixmap.scaled(20, 20))
        else:
            pass
    
    def get_mops_device(self):
        sender = self.sender().objectName()
        _cic_id = sender[1:-4]
        _mops_num = sender[3:-2]
        _port_id = sender[-1]
        status = self.check_mops(c=_cic_id, b=int(_port_id), m=_mops_num)
        if status:
            self.show_deviceWindow(cic=_cic_id, mops=_mops_num, port=str(_port_id)) 
            
        else:
            msg = "CIC " + _cic_id, "MOPS " + _mops_num, "Port " + _port_id, ": Not Found"
            self.set_textBox_message(comunication_object="ErrorFrame" , msg=str(msg)) 

        
    def update_mopshub_adc_channels_random(self,c,b,m):
        _dictionary = self.__dictionary_items
        _adc_indices = list(self.__adc_index)
        self.csv_writer = csv.writer(self.out_file_csv[c][b][m])
        
        for i in np.arange(len(_adc_indices)):
            _subIndexItems = list(AnalysisUtils().get_subindex_yaml(dictionary=_dictionary, index=_adc_indices[i], subindex="subindex_items"))
            _start_a = 3  # to ignore the first subindex it is not ADC
            for subindex in np.arange(_start_a, len(_subIndexItems) + _start_a - 1):
                s = subindex - _start_a
                ts = time.time()
                elapsedtime = ts -  self.__mon_time
                data_point = np.random.randint(0,100)     
                #data_point = "(c%s|b%s|m%s|s%s)"%(c,b,m,s)   
                self.csv_writer.writerow((str(round(elapsedtime, 1)),
                                     str(0),
                                     str("id"),
                                     str(subindex),
                                     str(data_point),
                                     str(round(data_point, 3)))) 
                self.channelValueBox[c][b][m][s].setText(str(data_point))   
                if self.trendingBox[c][b][m][s] == True:
                    if len(self.x[s]) >= 20:# Monitor a window of 100 points is enough to avoid Memory issues 
                        self.DataMonitoring.reset_data_holder(data_point,s) 
                    self.DataMonitoring.update_figure(data=data_point, subindex=subindex, graphWidget = self.graphWidget[s])
            #This will be used later for limits 
            if data_point >=95:
                self.update_alarm_limits(high=True, low=None, normal=None, object=self.channelValueBox[c][b][m][s]) 
                self.update_alarm_status(on=False, off=True, warning=False, button=self.mops_alarm_led[c][b][m],button_type = "Movie")
            elif (data_point >=50 and data_point <=80):
                self.update_alarm_limits(high=None, low=True, normal=None, object=self.channelValueBox[c][b][m][s])
                self.update_alarm_status(on=False, off=False, warning=True, button=self.mops_alarm_led[c][b][m],button_type = "Movie")
            else:
                self.channelValueBox[c][b][m][s].setStyleSheet("color: black;")
                self.update_alarm_status(on=True, off=False, warning=False, button=self.mops_alarm_led[c][b][m],button_type = "Movie")
         
        _conf_indices = list(self.__conf_index)                      
        a = 0 
        for i in np.arange(len(_conf_indices)):
            _subIndexItems = list(AnalysisUtils().get_subindex_yaml(dictionary=_dictionary, index=_conf_indices[i], subindex="subindex_items"))
            for s in np.arange(0, len(_subIndexItems)):
                adc_value = np.random.randint(0,100)
                self.confValueBox[c][b][m][a].setText(str(adc_value))      
                if adc_value <=95:
                    self.confValueBox[c][b][m][a].setStyleSheet("color: black;")
                else:
                    self.confValueBox[c][b][m][a].setStyleSheet(" background-color: red;")
                a = a + 1    
        
        _mon_indices = list(self.__mon_index)    
        a = 0
        for i in np.arange(len(_mon_indices)):
            _subIndexItems = list(AnalysisUtils().get_subindex_yaml(dictionary=_dictionary, index=_mon_indices[i], subindex="subindex_items"))
            for s in np.arange(0, len(_subIndexItems)):
                adc_value = np.random.randint(0,100)
                self.monValueBox[c][b][m][a].setText(str(adc_value))
                if adc_value <=95:
                    self.monValueBox[c][b][m][a].setStyleSheet("color: black;")
                else:
                    self.monValueBox[c][b][m][a].setStyleSheet(" background-color: red;")
                a = a + 1   
  
        
    def show_trendWindow(self,c,b,m):
        trend = QMainWindow(self)
        subindex = self.sender().objectName()
        s = int(subindex) - 3     
        self.trendingBox[c][b][m][s] = True  
        n_channels = 33
        for i in np.arange(0, n_channels): self.graphWidget[i].clear()  # clear any old plots
        self.x, self.y = self.DataMonitoring.trend_child_window(childWindow=trend, subindex=int(subindex), n_channels=n_channels)
        trend.show()
               
if __name__ == "__main__":
#self.update_bus_status_box(cic_id=c, port_id=b, off=True)#Special function to update the bus state
    pass
