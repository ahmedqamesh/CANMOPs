########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 01.05.2020
"""
########################################################

from __future__ import division
import numpy as np
import logging
import numba
import tables as tb
from scipy.optimize import curve_fit
class Analysis(object):
    
    def __init__(self):
        pass
    # Conversion functions
    def adc_conversion(self, adc_channels_reg="V", value=None,resistor_ratio = None,ref_voltage = None):
        '''
        the function will convert each ADC value into a reasonable physical quantity in volt
        > MOPS has 12 bits ADC value ==> 2^12 = 4096 (this means that we can read from 0 -> 4096 different decimal values)
        > The full 12 bits ADC covers up to 850mV [or ref_voltage]
        >This means that each ADC value corresponds to 850/4096 = 0.207 mV for 1 bit this is the resolution of the ADC)
        > The true voltage on each ADC is V = value * resistance
        Example: 
        To calibrate each ADC value 
        1. multiply by 0.207 to give the answer in mV
        2. multiply by the resistor ratio to get the actual voltage
        '''
        if value is not None:
            if adc_channels_reg == "V":
                value = value * ref_voltage/4096  *resistor_ratio
            elif adc_channels_reg == "T":
                value = value * ref_voltage/4096 * resistor_ratio  
            else:
                value = value
        return value

    def NTC_convertion(self,value =None):
        '''
        To convert ADC data to temperature you first find the thermistor resistance and then use it to find the temperature.
        https://www.jameco.com/Jameco/workshop/techtip/temperature-measurement-ntc-thermistors.html
        Rt = R0 * (( Vs / Vo ) - 1) 
        
        '''       
        return value
    
    
    def binToHexa(self, n):
        # convert binary to int
        num = int(n, 2)   
        # convert int to hexadecimal
        hex_num = hex(num)
        return(num)
    
if __name__ == "__main__":
        pass
