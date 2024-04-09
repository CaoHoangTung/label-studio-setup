# -*- coding: utf-8 -*-
"""
Created on Tue Jan 14 16:13:23 2023

@author: Lloyd LY CHAN
"""
import os
import numpy as np
import warnings
from Extraction import ExtractData,find_class_index, get_speed,window_index_8_step,get_porportion_walks_GT
from Classification import get_MLfeatures, Predict
from Regression import Steps_in_window
import pickle
from openmovement.load import CwaData
from openmovement.process import OmConvert
import math 
import bisect
import json
from pathlib import Path

DATA_PATH = "./label-studio-setup/data"

# Obtain required AX3 files
file_list=[]
for file in os.listdir(DATA_PATH):
    if file.endswith(".cwa")|file.endswith(".CWA")|file.endswith(".csv")|file.endswith(".CSV"):
        file_list.append(os.path.join(DATA_PATH, file))
print('----------Initiate Digital Gait Biomarker Extraction----------')
print('--------------------------Version:2.0-------------------------')
print('-----Program developed by Lloyd LY CHAN and Martin SH Lee-----')
print('--------------------------------------------------------------')
for datafile in file_list: # Loop for each participant
    # datafile = file_list[0]#assign cva file location
    if datafile.endswith(".cwa")|datafile.endswith(".CWA"):
        #Convert cwa format into ndarray
        om = OmConvert()
        with CwaData(datafile, include_gyro=False, include_temperature=True) as cwa_data: #Convert cwa format into ndarray
            # As an ndarray of [time,accel_x,accel_y,accel_z,temperature]
            sensor_data = cwa_data.get_sample_values()
            # As a pandas DataFrame
            samples = cwa_data.get_samples()
        record_start_time=samples['time'][0]
    else:
        print("Skipping")
        continue
   
    sensor_data_time=sensor_data[:,0]#Unix Epoch Time
        #Check number of days covered
    NumofDay_float=(sensor_data_time[-1]-sensor_data_time[0])/60/60/24
        #raise error if too little information was captured
    # if NumofDay_float<0.9:#raise error if too little information was captured
    #     raise Exception("Error: Less than 24 hours captured in the current .cwa file")
    
    #Get number of days captured in an integer
    NumofDay=math.ceil(NumofDay_float)
    rawFilePath, participant_id = os.path.split(datafile)
    participant_id = participant_id.split('.')[0]  #--> Remove any extension
    #Get time
    formatted_time = record_start_time.strftime("%Y%b%d(%a)%H:%M")
    formatted_date = record_start_time.strftime("%Y%b%d")
    starting_hour = int(record_start_time.strftime("%H"))+int(record_start_time.strftime("%M"))/60
    for DaySequence in range(1, NumofDay+1): #DaySequence is not in zero indexing to avoid confusion
        print('Processing---Participant ID:',participant_id,'---Day',DaySequence,'of', NumofDay, ' ---',len(file_list)-1,'more participant(s) remaining')
        dayStartRowIndex=bisect.bisect_left(sensor_data_time, sensor_data_time[0]+(DaySequence-1)*60*60*24)
        #Index of the last Row of that 24-hour period
        dayLastRowIndex=bisect.bisect_left(sensor_data_time, sensor_data_time[0]+(DaySequence)*60*60*24-1)
        day_sensor_data=sensor_data[dayStartRowIndex:dayLastRowIndex,0:4]
        # Extract AX3 data & DC-block removed VM
        AX3_application, AX3Data, AX3Data_Bandpass, sleep_period_time_hr, bedtime,NWT_hr = ExtractData(day_sensor_data, DaySequence,participant_id,starting_hour) 
        #[AX3_application, AX3Data, AX3Data_Bandpass, sleep_period_time_hr, bedtime,NWT_hr]= pickle.load(open('../../debug_6.sav', 'rb'))
        print('AX3 data pre-processed')
        import IPython ; IPython.embed()
    break