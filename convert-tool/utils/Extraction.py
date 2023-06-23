# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 20:23:47 2023

@author: Lloyd LY Chan
"""

import os
import sys
import numpy as np
import pickle
from numpy import linalg as LA
from scipy.signal import butter, filtfilt, lfilter
from math import floor
from openmovement.load import CwaData
from .Regression import Steps_in_window
from sklearn.preprocessing import StandardScaler

def butter_lowpass_filter(data, normal_cutoff, order):
    # Get the filter coefficients 
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    
    # Return filtered signal
    y = filtfilt(b, a, data)
    return y

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    # Get the filter coefficients 
    b, a = butter(order, [lowcut, highcut], fs=fs, btype='band')
    
    # Return filtered signal
    y = lfilter(b, a, data)
    return y

def import_npy(file):
    """
    Extracts data and time arrays from the saved numpy workspace.

    Parameters
    ----------
    file : string
        A string containing .cwa file name (including .cwa extension).

    Returns
    -------
    data : numpy array object
        A numpy.ndarray object containing x,y and z readings.
    time : numpy array object
        A numpy.ndarray object containing time stamps.

    """
    data_object = np.load(file[:-4]+'.npy')
    time = data_object['time']
    data = np.zeros([len(data_object), 3])
    data[:,0] = data_object['x']
    data[:,1] = data_object['y']
    data[:,2] = data_object['z']
    return data, time


def ExtractData(day_cwa, Day,rawFileName,starting_hour):
    """
    Extracts pre-processed accelerometer data from raw data .cwa file.

    Parameters
    ----------
    filepath : string
        A string containing .cwa file path (including .cwa extension).
    Day : integer
        An integer representing the day of interest.

    Returns
    -------
    

    """
    # Raw accelerometer data extraction
    gravity = 9.81
    AX3stream_raw = day_cwa[:,1:4] * gravity #--> Unit adjusted
    time = day_cwa[:,0] #--> Time limited to attention span

    # Append acceleration magnitude to readings
    AX3stream_raw = np.append(AX3stream_raw, LA.norm(AX3stream_raw, axis=1).reshape((-1, 1)), axis = 1)

    # Removing the DC componenet from the vector magnitude (ref to ieee 7552572)  The next three lines are significantly slower than the matlab code
    DC_rem = np.empty(AX3stream_raw.shape[0])
    
    # Compute the initial 20 values using a sliding window
    DC_rem[:20] = AX3stream_raw[:20, 3] - np.mean(AX3stream_raw[1:20, 3])
    
    # Compute the remaining values using a rolling mean
    window_mean = np.convolve(AX3stream_raw[:, 3], np.ones(20), mode='valid')[1:] / 20
    DC_rem[20:] = AX3stream_raw[20:, 3] - window_mean
    AX3stream_raw = np.column_stack([AX3stream_raw, DC_rem])
    # Butterworth low-pass filter
    order=5
    cutoff = 20 / (50 / 2)
    b, a = butter(order, cutoff, analog=False, btype='low')
    AX3stream_raw_butter0 = lfilter(b, a, AX3stream_raw[:, 0])
    AX3stream_raw_butter1 = lfilter(b, a, AX3stream_raw[:, 1])
    AX3stream_raw_butter2 = lfilter(b, a, AX3stream_raw[:, 2])
    AX3stream_raw_butter3 = lfilter(b, a, AX3stream_raw[:, 3])
    AX3stream_raw_butter4 = lfilter(b, a, AX3stream_raw[:, 4])
    AX3stream_raw_butter = np.concatenate((AX3stream_raw_butter0.reshape((-1, 1)), AX3stream_raw_butter1.reshape((-1, 1)), \
                                           AX3stream_raw_butter2.reshape((-1, 1)), AX3stream_raw_butter3.reshape((-1, 1)),\
                                        AX3stream_raw_butter4.reshape((-1, 1))), axis=1)
    
    # Alternative: Band-pass filter
    AccData = {"AX3stream_BandPass": butter_bandpass_filter(AX3stream_raw[:, 4], 0.25, 2.5, 100, order=5)}

    # Resampling
    #const = 1 / (24 * 60 * 60 * 100) #--> Conversion constant
    #tn = np.arange(0, time.shape[0] * const, const) 
    #time_series = (time - time[0])*1000*const #--> Non-ideal time count coming from watch (Unit: nsec-->sec)
    ideal_time=np.arange(0.02,time[-1]-time[0],0.01)#--> Ideal time count #Use 0.02 instead of 0 because first reading is usually noisy 
    time_series = (time - time[0]) #--> Non-ideal time count coming from watch
    _, ind = np.unique(time_series, return_index=True) #--> Get indices of unique time stamps
    AX3_0 = AX3stream_raw_butter[:, 0]
    AX3_1 = AX3stream_raw_butter[:, 1]
    AX3_2 = AX3stream_raw_butter[:, 2]
    AX3_3 = AX3stream_raw_butter[:, 3]
    AX3_4 = AX3stream_raw_butter[:, 4]
    AX3_0_int = np.interp(ideal_time, time_series[ind], AX3_0[ind]).reshape(-1, 1)
    AX3_1_int = np.interp(ideal_time, time_series[ind], AX3_1[ind]).reshape(-1, 1)
    AX3_2_int = np.interp(ideal_time, time_series[ind], AX3_2[ind]).reshape(-1, 1)
    AX3_3_int = np.interp(ideal_time, time_series[ind], AX3_3[ind]).reshape(-1, 1)
    AX3_4_int = np.interp(ideal_time, time_series[ind], AX3_4[ind]).reshape(-1, 1)
    AccData["AX3stream"] = np.concatenate((AX3_0_int, AX3_1_int, AX3_2_int, AX3_3_int, AX3_4_int), axis = 1)
            #--> Butterworth filtered data resampled
    AccData["AX3stream_BandPass"] = np.interp(ideal_time, time_series[ind], AccData["AX3stream_BandPass"][ind])
        #--> Bandpass filtered data resampled

    # Extract Directed routine AX3 stream data and cut it into 4-second windows
    window_size = 400 #--> Window size in points, given 100 HZ sampling rate and 4-sec. window
    win_num = floor(ideal_time.shape[0] / window_size) #--> Total number of windows
    AX3_application = {"subj_id": [rawFileName] * win_num, \
                       "AX3data": [AccData["AX3stream"][i:window_size + i, :] for i in range(0, (win_num - 1) * window_size + 1, window_size)], \
                       "AX3data_BandPass": [AccData["AX3stream_BandPass"][i:window_size + i] for i in range(0, (win_num - 1) * window_size + 1, window_size)], \
                       "timept": [np.array([i + 1, i + window_size]) for i in range(0, (win_num - 1) * window_size + 1, window_size)]}
        
    # Extract AX3stream
    AX3dataout = AccData["AX3stream"]
    AX3dataout2 = AccData["AX3stream_BandPass"]
    
    # Calculate and Extract Non-wear time(NWT) and Sleep Period Time (SPT)
    non_wear_threshold = 13/1000
    AX3_application["angle_z"]=[]
    AX3_application["non_wear"] =[]
    for i in range(0, len(AX3_application["AX3data"])):
        ax = np.array([np.median(AX3_application["AX3data"][i][:, 1] / gravity) ])
        ay = np.array([np.median(AX3_application["AX3data"][i][:, 2] / gravity) ])
        az = np.array([np.median(AX3_application["AX3data"][i][:, 3] / gravity) ])
        ax_std = np.array([np.std(AX3_application["AX3data"][i][:, 1] / gravity) ])
        ay_std = np.array([np.std(AX3_application["AX3data"][i][:, 2] / gravity) ])
        az_std = np.array([np.std(AX3_application["AX3data"][i][:, 3] / gravity) ])
        AX3_application["angle_z"]=np.append(AX3_application["angle_z"],np.arctan(az / (ax ** 2 + ay ** 2)) * (180 / np.pi))
        AX3_application["non_wear"] = np.append(AX3_application["non_wear"] ,[np.logical_and(ax_std < non_wear_threshold, ay_std < non_wear_threshold,az_std < non_wear_threshold).tolist()])
        
    # NWT Find consecutive non-wear time exceeding 60 minutes----------------------------LC2023May05: The following 6 lines does not produce same result as matlab code, please check and modify--------------
    NW = np.array(AX3_application["non_wear"])
    nw_end = np.where((np.append(0, NW) - np.append(NW, 0))[1:] == 1)[0]
            #--> Index of watch non-wearing end
    nw_end = np.append(0, nw_end) #--> Append the start of recording moment
    length = np.array([np.sum(NW[nw_end[i]+1:nw_end[i+1]+1]) for i in range(nw_end.shape[0]-1)])
            #--> Length of non-wear windows in the dataset
    exclude_ID = np.where(length > 900)[0] #--> Windows to be excluded ID
    exclude_idx_app = [] #--> Index of elements to be deleted from AX3_application
    exclude_idx_data = [] #--> Index of elements to be deleted from AX3dataout and AX3dataout2
    for i in range(exclude_ID.shape[0]):
        exclude_idx_app.extend(list(range(nw_end[exclude_ID[i] + 1] + 1 - int(length[exclude_ID[i]]), nw_end[exclude_ID[i] + 1] + 1)))
        exclude_idx_data.extend(list(range(nw_end[exclude_ID[i] + 1] * 400 + 1 - int(length[exclude_ID[i]]) * 400, nw_end[exclude_ID[i] + 1] * 400 + 1)))
    
    # NWT Delete non-wear time
    AX3_application["subj_id"] = np.delete(AX3_application["subj_id"], exclude_idx_app, 0).tolist()
    AX3_application["AX3data"] = np.delete(AX3_application["AX3data"], exclude_idx_app, 0)
    AX3_application["AX3data_BandPass"] = np.delete(AX3_application["AX3data_BandPass"], exclude_idx_app, 0)
    AX3_application["timept"] = np.delete(AX3_application["timept"], exclude_idx_app, 0)
    AX3_application["angle_z"] = np.delete(AX3_application["angle_z"], exclude_idx_app, 0).tolist()
    AX3_application["non_wear"] = np.delete(AX3_application["non_wear"], exclude_idx_app, 0).tolist()

    # Delete NWT bouts from AX3dataout & AX3Dataout2
    AX3dataout = np.delete(AX3dataout, exclude_idx_data, 0)
    AX3dataout2 = np.delete(AX3dataout2, exclude_idx_data, 0)
    
    # NWT export total NWT in hours
    if len(exclude_idx_app) == 0:
        NWT = 0 #--> Watch was worn at all times
    else:
        NWT = len(exclude_idx_app) / 900 #--> Get number of hours of non-wear time
    
    # SPT Step 4
    AX3_application["abs_diff"] = np.append(0, np.abs(np.diff(AX3_application["angle_z"]))).tolist()
    
    # SPT Step 5
    AX3_application["roll_median"] = [np.median(AX3_application["abs_diff"][p:p+75]) for p in range(len(AX3_application["abs_diff"]) - 75)]
    
    # SPT Step 6
    sleep_threshold = np.percentile(AX3_application["roll_median"], 10) * 15
    AX3_application["static"] = (np.array(AX3_application["roll_median"]) < sleep_threshold).tolist()
    
    # SPT Step 7
    # Get sleep hours and remove sleep data from dataset
    SS = np.array(AX3_application["static"]) #--> Static label array (True = static, False = dynamic)
    ss_end = np.where((np.append(0, SS) - np.append(SS, 0))[1:] == 1)[0]
            #--> Index of sleep period end
    ss_end = np.append(0, ss_end) #--> Append the start of recording moment
    length = np.array([np.sum(SS[ss_end[i]+1:ss_end[i+1]+1]) for i in range(ss_end.shape[0]-1)])
            #--> Length of sleep windows in the dataset
    #Get bedtime of the longest sleep 
    bedtime=(ss_end[length.argmax()+1]-length.max())/900+starting_hour
    exclude_ID = np.where(length > 450)[0] #--> Windows to be excluded ID (sleep period = 30 minutes)
    exclude_idx_app = [] #--> Index of elements to be deleted from AX3_application
    exclude_idx_data = [] #--> Index of elements to be deleted from AX3dataout and AX3dataout2
    for i in range(exclude_ID.shape[0]):
        exclude_idx_app.extend(list(range(ss_end[exclude_ID[i] + 1] + 1 - length[exclude_ID[i]], ss_end[exclude_ID[i] + 1] + 1)))
        exclude_idx_data.extend(list(range(ss_end[exclude_ID[i] + 1] * 400 + 1 - length[exclude_ID[i]] * 400, ss_end[exclude_ID[i] + 1] * 400 + 1)))
    
    # Sleep Delete time
    AX3_application["subj_id"] = np.delete(AX3_application["subj_id"], exclude_idx_app, 0).tolist()
    AX3_application["AX3data"] = np.delete(AX3_application["AX3data"], exclude_idx_app, 0)
    AX3_application["AX3data_BandPass"] = np.delete(AX3_application["AX3data_BandPass"], exclude_idx_app, 0)
    AX3_application["timept"] = np.delete(AX3_application["timept"], exclude_idx_app, 0)
    AX3_application["angle_z"] = np.delete(AX3_application["angle_z"], exclude_idx_app, 0).tolist()
    AX3_application["non_wear"] = np.delete(AX3_application["non_wear"], exclude_idx_app, 0).tolist()
    
    # Delete NWT bouts from AX3dataout & AX3Dataout2
    AX3dataout = np.delete(AX3dataout, exclude_idx_data, 0)
    AX3dataout2 = np.delete(AX3dataout2, exclude_idx_data, 0)
    
    # Export total sleep period in hours
    if len(exclude_idx_app) == 0:
        sleep_hr = 0 #--> No sleep
    else:
        sleep_hr = len(exclude_idx_app) / 900 #--> Get number of hours of sleep
        
    # Remove redundant disctionary entries/keys
    del AX3_application['angle_z']; del AX3_application['abs_diff'];
    del AX3_application['roll_median']; del AX3_application['static'];

    return AX3_application, AX3dataout ,AX3dataout2, sleep_hr,bedtime, NWT
    
# Test
#AX3_application, AX3dataout ,AX3dataout2, sleep_hr, NWT = ExtractData('C:/Users/Samer/Desktop/Upwork/Projects/Code migration task/3Extraction Python/example.cwa', 1)                 

def find_class_index(row_to_search, class_to_find):
    """
    Extracts data and time arrays from the saved numpy workspace.

    Parameters
    row_to_search: array
        Example: last column of MLdata, which is the predicted class
    class_to_find : array
        Example: [1,2,3,4,5,6] or 1

    Returns
    -------
    consecutive list: numpy array object
        A numpy.ndarray object containing a list of lists of start and end of consecutive window indices

    """
    indices=[]
    for idx, value in enumerate(row_to_search):
        if value in class_to_find:
            indices.append(idx+1) #Since MLdata starts from the second row of AX3 application and ends at second last row, it has to +1 to match AX3application row
    consecutive_list=np.split(indices, np.where(np.diff(indices) != 1)[0]+1)
    return consecutive_list

def get_speed(walk_index,AX3_application,height_cm,reg_1,scaler):
    iqr_acc=[];range_acc=[];steptime=[];est_Speed=[]
    #for-loop through all walking windows
    for  speed_i in range(0,len(walk_index)):
        #Get window-size band-pass filtered acceleration signal
        window_ax3_bandpass=AX3_application['AX3data_BandPass'][walk_index[speed_i],:]
        #Get window-size butterworth-filtered acceleration signal
        window_ax3_butter=AX3_application['AX3data'][walk_index[speed_i],:,:]
        #Get interquartile range of acceleration signal amplitude
        q3,q1=np.percentile(window_ax3_butter[:,4],[75,25])
        window_iqr_acc=q3-q1
        #Get median of acceleration signal amplitude
        window_median_acc=np.percentile(window_ax3_butter[:,4],50)
        # Get mean of crude vector magnitude of acceleration signal amplitude
        window_crude_mean=np.mean(window_ax3_butter[:,3])
        #Get range of acceleration signal amplitude
        window_range_acc=np.ptp(window_ax3_butter[:,4])
        #Get local timestamp of heel strikes
        window_step_time, _, _, _, window_ploc=Steps_in_window(window_ax3_bandpass)
        if np.isnan(window_step_time):
            window_step_time=4
        #Get correlation coefficient between acceleration signal in x-axis and y-axis
        window_corr_x_y=np.corrcoef(window_ax3_butter[:, 0], window_ax3_butter[:, 1])[0, 1]
        #Get correlation coefficient between acceleration signal in y-axis and z-axis
        window_corr_x_z=np.corrcoef(window_ax3_butter[:, 0], window_ax3_butter[:, 2])[0, 1]
        #Get Speed
        #Return list of predictors 
        mypredictors=np.array([     height_cm,\
                                    window_iqr_acc**.25,\
                                    window_step_time**-.5,\
                                    window_median_acc,\
                                    window_corr_x_y,\
                                    window_corr_x_z,\
                                    window_crude_mean**-4]).reshape(1,-1)
        scaled_mypredictors=scaler.transform(mypredictors)
        window_est_Speed=reg_1.predict(scaled_mypredictors)
        est_Speed=np.append(est_Speed, window_est_Speed, axis = 0)
        iqr_acc=np.append(iqr_acc, [window_iqr_acc], axis = 0)
        range_acc=np.append(range_acc, [window_range_acc], axis = 0)                            
        steptime=np.append(steptime,[window_step_time] , axis = 0)
    return est_Speed,iqr_acc,range_acc, steptime

def window_index_8_step(walk_index_list, AX3_application):
    walk_index_8step = []
    AX3_8step= []
    for i in range(len(walk_index_list)):
        continuous_ax3_bandpass=[]
        for j in range(len(walk_index_list[i])):
            window_ax3_bandpass=AX3_application['AX3data_BandPass'][walk_index_list[i][j],:]
            continuous_ax3_bandpass=np.concatenate((continuous_ax3_bandpass, window_ax3_bandpass))
            _,_,_,_,heelstrike_local_timestamp=Steps_in_window(continuous_ax3_bandpass)
            # #plt.plot(continuous_ax3_bandpass)

            # # Overlay vertical lines
            # plt.vlines(heelstrike_local_timestamp, ymin=-2, ymax=2, color='red',linewidth=0.5)
            # plt.show()
            loop = 1
            n = len(heelstrike_local_timestamp)
            while n >= 9:
                start_pt = heelstrike_local_timestamp[(loop - 1) * 8]
                end_pt = heelstrike_local_timestamp[loop * 8]
                step_time=np.diff(heelstrike_local_timestamp[(loop - 1) * 8:loop * 8 ])/ 100
                step_time_mean=np.nanmean(step_time)
                cadence=60/step_time_mean
                step_time_std = np.std(step_time)
                walk_index_8step.append((start_pt, end_pt,cadence, step_time_std,step_time))
                AX3_8step.append(continuous_ax3_bandpass[start_pt.astype(int):end_pt.astype(int)])
                loop += 1
                n -= 8
    return walk_index_8step,AX3_8step

def get_porportion_walks_GT(window_index_list,at_least_x_sec):
    
    min_nWindow=int(at_least_x_sec)/4
    count = 0
    for array in window_index_list:
        if len(array) >= min_nWindow:
            count += 1
    # Calculate the proportion
    proportion = 1-count / len(window_index_list)
    
    return proportion