# -*- coding: utf-8 -*-
"""
Created on Wed Dec 26 22:04:20 2022

@author: Samer Ahmed (https://github.com/SamMans)
"""
import numpy as np
from sklearn import svm, preprocessing
#from sklearn.model_selection import KFold
from scipy.signal import find_peaks, argrelextrema
from sklearn.tree import DecisionTreeRegressor

from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
import matplotlib
import matplotlib.pyplot as plt
from sklearn import linear_model
from sklearn.model_selection import train_test_split,cross_val_score, cross_val_predict
from sklearn import svm

def Join(A, B, keyA, keyB):
    """
    Returns An inner-join dictionary (like the inner-join function in matlab).

    Parameters
    ----------
    A : python dictionary
        A dictionary containing data with one common key as B.
    B : python dictionary
        A dictionary containing data with one common key as A.
    keyA : string
       Dictionary matching key for A.
    keyB : string
       Dictionary matching key for B.

    Returns
    -------
    C : python dictionary
        An inner-join dictionary of A and B.

    """
    idxB = np.array([np.where(np.array(B[keyB]) == np.array(A[keyA][i]))[0] \
                    for i in range(0, len(A[keyA])) \
                        if np.where(np.array(B[keyB]) == np.array(A[keyA][i]))[0].shape[0] == 1]).reshape(-1,)
            #--> Matching indices in B to A
    idxA = np.array([i for i in range(0, len(A[keyA])) \
                     if np.where(np.array(B[keyB]) == np.array(A[keyA][i]))[0].shape[0] == 1]).reshape(-1,)      
    C = {} #--> Empty dictionary "to be filled"
    for i in A:
        try: 
            C[i] = np.array(A[i])[idxA].tolist()
        except ValueError:
            C[i] = np.array(A[i], dtype=np.ndarray)[idxA].tolist() 
            #--> Append matching elements from first dict.
    for i in B:
        C[i] = np.array(B[i])[idxB].tolist() 
                #--> Append matching elements from second dict.
    return C

def Steps_in_window(A):
    """
    Returns a set of time domain properties extracted from a time series.

    Parameters
    ----------
    A : numpy array of float64
        A 1D array containing data.

    Returns
    -------
    avgsteptime_sec : float64
        Average step time in seconds.
    vector_step_time_sec : numpy array of float64
        A 1D array containing step times.
    step_regularity : float64
        Step regularity.
    strike_regularity : float64
        Strike regularity.
    ploc :numpy array of float64
        A 1D array containing locations.

    """
    p_threshold = np.mean(A) + np.std(A) * 0.5
    v_threshold = 0
    
    # find heelstrike timepoints with findpeak in accelration pattern
    locs = find_peaks(A, height=p_threshold, distance=33)[0] #--> Peak locations
    v_loc = argrelextrema(A, np.less)[0] #--> Get local minima indices
    v_loc = np.delete(v_loc, np.where(A[v_loc] > -v_threshold)[0])
    
    # check if local maxima and local minima are alternating
    ploc = np.array([]); vloc = np.array([]);
    if locs.shape[0] != 0 and v_loc.shape[0] != 0:
        if locs[0] < v_loc[0]:
            ploc = np.append(ploc, locs[0])
            
    while True:
        if locs.shape[0] == 0 or v_loc.shape[0] == 0:
            break
        tempvloc = v_loc[0]
        if locs[0] > tempvloc:
            v_loc = np.delete(v_loc, 0)
            ploc = np.append(ploc, locs[0])
        if locs.shape[0] == 0 or v_loc.shape[0] == 0:
            break
        tempploc = locs[0]
        if v_loc[0] > tempploc:
            locs = np.delete(locs, 0)
            vloc = np.append(vloc, v_loc[0])
    ploc=sorted(list(set(ploc)))
    vloc=sorted(list(set(vloc)))
    temp_vector_step_time_sec = np.diff(np.unique(ploc)) / 100
    temp_avgsteptime_sec = np.mean(temp_vector_step_time_sec)
    
    # find step-time with auto-correlation
    r = np.correlate(A, A, 'full') #--> Auto correlation for DC block
    LOCS = find_peaks(r, prominence=70, distance=33)[0] #--> Peak locations
    # for exception that no peak is found within the auto-correlation plot
    if LOCS.shape[0]>0:
        PKS = r[LOCS] #--> Peak values
        r0 = np.amax(PKS) #--> Maximum peak
        index_r0 = np.where(PKS == r0)[0][0] #--> Index of maximum peak
    
        # The first peak of autocorrelation indicates a correlation between
        # steps and is therefore considered the step regularity (AKA symmetry index).
        if PKS.shape[0] - 1 >= index_r0 + 1:
            step_regularity = PKS[index_r0 + 1] / r0
        else:
            step_regularity = 0
        
        # The second peak represents a correlation between a stride and the next one, the second peak
        # of the autocorrelation can be considered as the stride regularity
        # (AKA regularity index).
        if PKS.shape[0] - 1 >= index_r0 + 2:
            strike_regularity = PKS[index_r0 + 2] / r0
        else:
            strike_regularity = 0
    
        # step-time
        if LOCS.shape[0] - 1 >= index_r0 + 1:
            autocorr_steptime_sec = (LOCS[index_r0 + 1] - LOCS[index_r0]) / 100
        else:
            autocorr_steptime_sec = 0
    else:
        step_regularity = 0; strike_regularity = 0; autocorr_steptime_sec = 0;
    
    
    if (temp_avgsteptime_sec-autocorr_steptime_sec)/ temp_avgsteptime_sec>0.05 or\
        (strike_regularity < step_regularity) or\
            (strike_regularity<0.3):
            # find heelstrike timepoints with findpeak in accelration pattern
            locs = find_peaks(A, height=(None), distance=33)[0] #--> Peak locations
            v_loc = argrelextrema(A, np.less)[0] #--> Get local minima indices
            
            # check if local maxima and local minima are alternating
            ploc = np.array([]); vloc = np.array([]);
            if locs.shape[0] != 0 and v_loc.shape[0] != 0:
                if locs[0] < v_loc[0]:
                    ploc = np.append(ploc, locs[0])
                    
            while True:
                if locs.shape[0] == 0 or v_loc.shape[0] == 0:
                    break
                tempvloc = v_loc[0]
                if locs[0] > tempvloc:
                    v_loc = np.delete(v_loc, 0)
                    ploc = np.append(ploc, locs[0])
                if locs.shape[0] == 0 or v_loc.shape[0] == 0:
                    break
                tempploc = locs[0]
                if v_loc[0] > tempploc:
                    locs = np.delete(locs, 0)
                    vloc = np.append(vloc, v_loc[0])
            ploc=sorted(list(set(ploc)))
            vloc=sorted(list(set(vloc)))
            new_vector_step_time_sec = np.diff(np.unique(ploc)) / 100
            new_avgsteptime_sec = np.mean(new_vector_step_time_sec)
            if np.diff(np.array([new_avgsteptime_sec, autocorr_steptime_sec])) < autocorr_steptime_sec * 0.03:
                vector_step_time_sec = new_vector_step_time_sec
                avgsteptime_sec = new_avgsteptime_sec
            else:
                vector_step_time_sec = temp_vector_step_time_sec
                avgsteptime_sec = temp_avgsteptime_sec
    else:
            vector_step_time_sec = temp_vector_step_time_sec
            avgsteptime_sec = temp_avgsteptime_sec
            
    return avgsteptime_sec, vector_step_time_sec, step_regularity, strike_regularity, ploc

def trainRegressionModel(trainingData):
    """
    Returns a trained regression model and its RMSE.

    Parameters
    ----------
    trainingData : numpy array of float64
        A 2D array containing training data (outputs, features).

    Returns
    -------
    clf : SVC object of sklearn.svm._classes module
        A classifier object that can be used to predict activities.
    validationAccuracy : float64
        A number specifying the mean of all k-fold validation accuracies.
    C : numpy array of int64
        A 2D array representing confusion matrix.

    """
    # Extract features and labels
    predictors = trainingData[:, 1:-1] #--> Training features
    response = trainingData[:, -1] #--> Training outputs
    
    # Build regression model
    q3, q1 = np.percentile(response, [75 ,25])
    responseScale = q3 - q1 #--> Calculate interquartile range of response
    if responseScale > 10000 or responseScale == 0.0:
        responseScale = 1.0 #--> Limit response scale to 1 if originally infinite/zero
    boxConstraint = responseScale / 1.349
    epsilon = responseScale / 13.49
    trainedModel = svm.SVR(kernel='linear', C=boxConstraint, epsilon=epsilon) #--> SVM object
    # Fit regression model
    trainedModel.fit(predictors, response)
    
    
    
    
    # Set up holdout validation
    # LC: to control intra-class correlation bias
    subj_num = np.unique(trainingData[:, 0]) #--> Every possible subject ID in dataset
    nFoldRMSE = np.array([]) #--> list of n-folds' validation accuracy
    Prediction = np.array([]) #--> List of validation predictions for all folds "initially empty"
    Known = np.array([]) #--> List of already known validation ground truth for all folds "initially empty"
    for nfold in range(0, 9):
        # Prepare nfold training and testing datasets
        indices = np.random.permutation(subj_num.shape[0]) #--> Shuffled indices
        CVthreshold = round(0.9 * indices.shape[0]) #--> Validation threshold between training and testing
        train_subj_id, test_subj_id = subj_num[indices[:CVthreshold]], subj_num[indices[CVthreshold:]] #--> Training/testing subject IDs
        training_idx, test_idx = np.where(np.isin(trainingData[:, 0], train_subj_id))[0], \
        np.where(np.isin(trainingData[:, 0], test_subj_id))[0] #--> Training/testing indices
        trainingPredictors, testPredictors = predictors[training_idx, :], \
        predictors[test_idx, :] #--> Training and testing features for nfold
        trainingResponse, testResponse = response[training_idx], response[test_idx] #--> nfold labels
        
        # Train classifier using training dataset
        cvModel= svm.SVR(kernel='linear', C=boxConstraint, epsilon=epsilon) #--> SVM object
        cvModel.fit(trainingPredictors, trainingResponse)
      
        # Predict response using test dataset
        testPredictions = cvModel.predict(testPredictors) #--> Validation prediction
        
        # Update list of validation predictions and ground truths
        Prediction = np.append(Prediction, testPredictions)
        Known = np.append(Known, testResponse)
        
        # Compute validation RMSE
        nFoldRMSE= np.append(nFoldRMSE, np.sqrt(np.sum(np.square(testResponse - testPredictions)) / testResponse.shape[0]))
                             
    # Compute overall validation accuracy
    validationRMSE = np.mean(nFoldRMSE)
    
    
    return trainedModel, validationRMSE

def z_transform_columns(data):
    num_rows, num_cols = data.shape
    z_scores = np.zeros_like(data, dtype=float)
    
    for col in range(num_cols):
        column = data[:, col]
        mean = np.mean(column)
        std_dev = np.std(column)
        z_scores[:, col] = (column - mean) / std_dev
        
    return z_scores

# Regression test
#x = np.random.randn(200, 46)
#y = np.sum(x, axis = 1)
#trainingData = np.append(x, y.reshape(-1, 1), axis = 1)
#model, rmse = trainRegressionModel(trainingData)
#lolo = model.predict(x)

# Test
#d = np.random.randn(2000,)
#avgsteptime_sec, vector_step_time_sec, step_regularity, strike_regularity, ploc = Steps_in_window(d)