# -*- coding: utf-8 -*-
"""
Created on Mon Dec 22 01:26:34 2022

@author: Samer Ahmed (https://github.com/SamMans)
"""

import numpy as np
from scipy.signal import find_peaks
from pywt import cwt, Wavelet
from sklearn import svm, preprocessing, metrics
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def get_MLfeatures(pre, current, post, subj_id, response):
    """
    Extracts features from raw data provided as input.

    Parameters
    ----------
    pre : numpy array
        A 2D array containing pre-window readings (index: k-1).
    current : numpy array
        A 2D array containing current window readings (index: k).
    post : numpy array
        A 2D array containing post window readings (index: k+1).
    subj_id : int
        An integer specifying subject ID.
    response : float
        A number specifying response.

    Returns
    -------
    temp_Data : numpy array
        A numpy.ndarray object, which contains extracted features.

    """
    # Initialize the features vector
    tempData = np.zeros(48, dtype = float) #--> Feature vector initialized to zeros
    
    # Fill in subject ID and response
    tempData[0] = subj_id
    tempData[1] = response
    
    # Pre-window analysis
    AX3data = pre #--> Analysis vector
    # DC block time domain features
    tempData[2] = np.amin(AX3data[:, 4], axis = 0) #--> Minimum of DC block
    tempData[3] = np.percentile(AX3data[:, 4], 50) #--> Median of DC block
    # Correlations
    tempData[4] = np.corrcoef(AX3data[:, 0], AX3data[:, 1])[0, 1] #--> x, y axes
    tempData[5] = np.corrcoef(AX3data[:, 0], AX3data[:, 2])[0, 1] #--> x, z axes
    tempData[6] = np.corrcoef(AX3data[:, 1], AX3data[:, 2])[0, 1] #--> y, z axes
    # Crude vector processing
    tempData[7] = np.amin(AX3data[:, 3], axis = 0) #--> Minimum of crude vector
    tempData[8] = np.percentile(AX3data[:, 3], 25) #--> 25th percentile of crude vector
    tempData[9] = np.percentile(AX3data[:, 3], 50) #--> 50th percentile of crude vector
    tempData[10] = np.percentile(AX3data[:, 3], 75) #--> 75th percentile of crude vector
    # Autocorrelation coefficient and step-time
    r = np.correlate(AX3data[:, 4], AX3data[:, 4], 'full') #--> Auto correlation for DC block
    LOCS = find_peaks(r, prominence=70, distance=33)[0] #--> Peak locations
    PKS = r[LOCS] #--> Peak values
    if PKS.shape[0] > 1:
        r0 = np.amax(PKS) #--> Maximum peak
        index_r0 = np.where(PKS == r0)[0][0] #--> Index of maximum peak
        autocorr_coef = PKS[index_r0 + 1]
        norm_autocorr_coef = autocorr_coef / r0
        autocorr_steptime = LOCS[index_r0 + 1] - LOCS[index_r0]
    else:
        autocorr_coef = 0
        norm_autocorr_coef = 0
        autocorr_steptime = 0
    if PKS.shape[0] > 6:
        ratio_autocorr_coef13 = abs(PKS[index_r0 + 1]) / PKS[index_r0 + 3]
        ratio_autocorr_coef12 = abs(PKS[index_r0 + 1]) / PKS[index_r0 + 2]
        ratio_autocorr_steptime12 = (LOCS[index_r0 + 1] - LOCS[index_r0]) / (LOCS[index_r0 + 2] - LOCS[index_r0 + 1])
        ratio_autocorr_steptime13 = (LOCS[index_r0 + 1] - LOCS[index_r0]) / (LOCS[index_r0 + 3] - LOCS[index_r0 + 2])
    else:
        ratio_autocorr_coef12 = 0
        ratio_autocorr_coef13 = 0
        ratio_autocorr_steptime12 = 0
        ratio_autocorr_steptime13 = 0
    tempData[11] = ratio_autocorr_steptime12 #--> Ratio autocorrelation
    
    # Current window analysis
    AX3data = current #--> Analysis vector
    # Wavelet coefficients feature
    scales = np.array([1, 12, 22, 37, 57, 85, 115, 165, 245]) 
    tempCoefAdjVecMag, freqs = cwt(AX3data[:, 4], scales, 'morl')
    tempCoefAdjVecMag = np.absolute(tempCoefAdjVecMag) #--> Take magnitude only without sign
    tempData[12] = np.mean(np.mean(tempCoefAdjVecMag[1:2, :], axis = 0)) #--> Add mean of coefficients (scales 12 to 22)
    tempData[13] = np.mean(np.mean(tempCoefAdjVecMag[3:4, :], axis = 0)) #--> Add mean of coefficients (scales 37 to 57)
    tempData[14] = np.mean(np.mean(tempCoefAdjVecMag[5:6, :], axis = 0)) #--> Add mean of coefficients (scales 85 to 115)
    tempData[15] = np.mean(np.mean(tempCoefAdjVecMag[7:8, :], axis = 0)) #--> Add mean of coefficients (scales 165 to 245)
    # DC block
    tempData[16] = np.mean(AX3data[:, 4]); #--> Mean of DC block
    tempData[17] = np.std(AX3data[:, 4], axis = 0); #--> Standard deviation of DC block
    tempData[18] = np.amax(AX3data[:, 4], axis = 0) #--> Maximum of DC block
    tempData[19] = np.percentile(AX3data[:, 4], 25) #--> 25th percentile of DC block
    tempData[20] = np.percentile(AX3data[:, 4], 50) #--> 50th percentile of DC block
    tempData[21] = np.percentile(AX3data[:, 4], 75) #--> 75th percentile of DC block
    # Correlations
    tempData[22] = np.corrcoef(AX3data[:, 1], AX3data[:, 2])[0, 1] #--> x, y axes
    # Crude vector
    tempData[23] = np.mean(AX3data[:, 3]) #--> Mean of crude vector
    tempData[24] = np.std(AX3data[:, 3], axis = 0) #--> Standard deviation of crude vector
    tempData[25] = np.percentile(AX3data[:, 3], 50) #--> 50th percentile of crude vector
    # Autocorrelation coefficient and step-time
    r = np.correlate(AX3data[:, 4], AX3data[:, 4], 'full') #--> Auto correlation for DC block
    LOCS = find_peaks(r, prominence=(70), distance=33)[0] #--> Peak locations
    PKS = r[LOCS] #--> Peak values
    if PKS.shape[0] > 1:
        r0 = np.amax(PKS) #--> Maximum peak
        index_r0 = np.where(PKS == r0)[0][0] #--> Index of maximum peak
        autocorr_coef = PKS[index_r0 + 1]
        norm_autocorr_coef = autocorr_coef / r0
        autocorr_steptime = LOCS[index_r0 + 1] - LOCS[index_r0]
    else:
        autocorr_coef = 0
        norm_autocorr_coef = 0
        autocorr_steptime = 0
    if PKS.shape[0] > 6:
        ratio_autocorr_coef13 = abs(PKS[index_r0 + 1]) / PKS[index_r0 + 3]
        ratio_autocorr_coef12 = abs(PKS[index_r0 + 1]) / PKS[index_r0 + 2]
        ratio_autocorr_steptime12 = (LOCS[index_r0 + 1] - LOCS[index_r0]) / (LOCS[index_r0 + 2] - LOCS[index_r0 + 1])
        ratio_autocorr_steptime13 = (LOCS[index_r0 + 1] - LOCS[index_r0]) / (LOCS[index_r0 + 3] - LOCS[index_r0 + 2])
    else:
        ratio_autocorr_coef12 = 0
        ratio_autocorr_coef13 = 0
        ratio_autocorr_steptime12 = 0
        ratio_autocorr_steptime13 = 0
    tempData[26] = norm_autocorr_coef #--> Normalized autocorrelation coefficient
    tempData[27] = autocorr_coef #--> Autocorrelation coefficient
    tempData[28] = ratio_autocorr_coef12 #--> Ratio between 1st and 2nd autocorrelation coefficient
    tempData[29] = ratio_autocorr_steptime12 #--> Ratio between 1st and 2nd autocorrelation time-lag
    tempData[30] = ratio_autocorr_coef13 #--> Ratio between 1st and 3rd autocorrelation coefficient
    tempData[31] = ratio_autocorr_steptime13 #--> Ratio between 1st and 3rd autocorrelation time-lag
    tempData[32] = autocorr_steptime #--> Time-lag of 1st autocorrelation
    
    # Post window analysis
    AX3data = post #--> Analysis vector
    # Wavelet coefficients feature
    scales = np.array([1, 12, 22, 37, 57, 85, 115, 165, 245]) 
    tempCoefAdjVecMag, freqs = cwt(AX3data[:, 4], scales, 'morl')
    tempCoefAdjVecMag = np.absolute(tempCoefAdjVecMag) #--> Take magnitude only without sign
    tempData[33] = np.mean(np.mean(tempCoefAdjVecMag[0:1, :], axis = 0)) #--> Add mean of coefficients (scales 1 to 12)
    tempData[34] = np.mean(np.mean(tempCoefAdjVecMag[3:4, :], axis = 0)) #--> Add mean of coefficients (scales 37 to 57)
    tempData[35] = np.mean(np.mean(tempCoefAdjVecMag[4:5, :], axis = 0)) #--> Add mean of coefficients (scales 57 to 85)
    tempData[36] = np.mean(np.mean(tempCoefAdjVecMag[6:7, :], axis = 0)) #--> Add mean of coefficients (scales 115 to 165)
    tempData[37] = np.mean(np.mean(tempCoefAdjVecMag[7:8, :], axis = 0)) #--> Add mean of coefficients (scales 165 to 245)
    # DC block
    tempData[38] = np.mean(AX3data[:, 4])
    tempData[39] = np.std(AX3data[:, 4], axis = 0); #--> Standard deviation of DC block
    tempData[40] = np.percentile(AX3data[:, 4], 25) #--> 25th percentile of DC block
    tempData[41] = np.percentile(AX3data[:, 4], 50) #--> 50th percentile of DC block
    # Correlations
    tempData[42] = np.corrcoef(AX3data[:, 0], AX3data[:, 2])[0, 1] #--> x, z axes
    # Crude vector
    tempData[43] = np.mean(AX3data[:, 3]) #--> Mean of crude vector
    tempData[44] = np.amax(AX3data[:, 3], axis = 0) #--> Maximum of crude vector
    tempData[45] = np.percentile(AX3data[:, 3], 50) #--> 50th percentile of crude vector
    tempData[46] = np.percentile(AX3data[:, 3], 75) #--> 75th percentile of crude vector
    # Autocorrelation coefficient and step-time
    r = np.correlate(AX3data[:, 4], AX3data[:, 4], 'full') #--> Auto correlation for DC block
    LOCS = find_peaks(r, prominence=(70), distance=33)[0] #--> Peak locations
    PKS = r[LOCS] #--> Peak values
    if PKS.shape[0] > 1:
        r0 = np.amax(PKS) #--> Maximum peak
        index_r0 = np.where(PKS == r0)[0][0] #--> Index of maximum peak
        autocorr_coef = PKS[index_r0 + 1]
        norm_autocorr_coef = autocorr_coef / r0
        autocorr_steptime = LOCS[index_r0 + 1] - LOCS[index_r0]
    else:
        autocorr_coef = 0
        norm_autocorr_coef = 0
        autocorr_steptime = 0
    if PKS.shape[0] > 6:
        ratio_autocorr_coef13 = abs(PKS[index_r0 + 1]) / PKS[index_r0 + 3]
        ratio_autocorr_coef12 = abs(PKS[index_r0 + 1]) / PKS[index_r0 + 2]
        ratio_autocorr_steptime12 = (LOCS[index_r0 + 1] - LOCS[index_r0]) / (LOCS[index_r0 + 2] - LOCS[index_r0 + 1])
        ratio_autocorr_steptime13 = (LOCS[index_r0 + 1] - LOCS[index_r0]) / (LOCS[index_r0 + 3] - LOCS[index_r0 + 2])
    else:
        ratio_autocorr_coef12 = 0
        ratio_autocorr_coef13 = 0
        ratio_autocorr_steptime12 = 0
        ratio_autocorr_steptime13 = 0
    tempData[47] = ratio_autocorr_steptime12 #--> Ratio between 1st and 2nd autocorrelation time-lag  
    
    return tempData

def trainClassifier(trainingData, k, label):
    """
    Extracts features from raw data provided as input.

    Parameters
    ----------
    trainingData : numpy array of float64
        A 2D array containing training data (labels, features).
    k : int
        An integer indicating the number of k-folds.
    label: list
        A list containing the names of actual classes.

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
    predictors = trainingData[:, 2:] #--> Training features
    response = trainingData[:, 1] #--> Training labels
    ClassLabels = np.unique(response) #--> Set of class labels
                
    # Classifier setup
    predictors = preprocessing.scale(predictors) #--> Standardize features
 
    # Set up holdout validation
    # LC: to control intra-class correlation bias
    subj_id = np.unique(trainingData[:, 0]) #--> Every possible subject ID in dataset
    nFoldValidAcc = np.array([]) #--> list of n-folds' validation accuracy
    Prediction = np.array([]) #--> List of validation predictions for all folds "initially empty"
    Known = np.array([]) #--> List of already known validation ground truth for all folds "initially empty"

    gridValidationsOuputs = {}
    param_grid = {'C': [1, 3, 5, 7, 10]}
    for c in param_grid['C']:
        subj_id = np.unique(trainingData[:, 0]) #--> Every possible subject ID in dataset
        nFoldValidAcc = np.array([]) #--> list of n-folds' validation accuracy
        Prediction = np.array([]) #--> List of validation predictions for all folds "initially empty"
        Known = np.array([]) #--> List of already known validation ground truth for all folds "initially empty"
        for nfold in range(0, k):
            # Prepare nfold training and testing datasets
            indices = np.random.permutation(subj_id.shape[0]) #--> Shuffled indices
            CVthreshold = round(0.9 * indices.shape[0]) #--> Validation threshold between training and testing
            train_subj_id, test_subj_id = subj_id[indices[:CVthreshold]], subj_id[indices[CVthreshold:]] #--> Training/testing subject IDs
            training_idx, test_idx = np.where(np.isin(trainingData[:, 0], train_subj_id))[0], \
            np.where(np.isin(trainingData[:, 0], test_subj_id))[0] #--> Training/testing indices
            trainingPredictors, testPredictors = predictors[training_idx, :], \
            predictors[test_idx, :] #--> Training and testing features for nfold
            trainingResponse, testResponse = response[training_idx], response[test_idx] #--> nfold labels
            
            # Train classifier using training dataset
            CVclf = svm.SVC(kernel='rbf', gamma='auto', C=c) #--> Validation SVM object
            if ClassLabels.shape[0] == 6:
                # In case you have 6 unique labels, assign weights to each class
                prior_dict ={ClassLabels[0]: 0.5, ClassLabels[1]: 6.67, ClassLabels[2]: 50, 
                            ClassLabels[3]: 3.22, ClassLabels[4]: 3.33, ClassLabels[5]: 33.3} #--> Prior weights
                # CVclf.set_params(class_weight="balanced")
                CVclf.set_params(class_weight = prior_dict) #--> Add prior weights parameter
                # Fit data
                CVclf.fit(trainingPredictors, trainingResponse)
            else:
                # In case you have more (or less) than 6 unique labels, fit right away
                CVclf.set_params(class_weight="balanced")
                CVclf.fit(trainingPredictors, trainingResponse)
            
            # Predict response using test dataset
            testPredictions = CVclf.predict(testPredictors) #--> Validation prediction
            
            # Update list of validation predictions and ground truths
            Prediction = np.append(Prediction, testPredictions)
            Known = np.append(Known, testResponse)
            # Compute validation accuracy
            accuracy = np.sum(testPredictions==testResponse) / (testPredictions==testResponse).shape[0]
            nFoldValidAcc = np.append(nFoldValidAcc, accuracy)
            print(f"C: {c}, nfold: {nfold}, Prediction Shape: {Prediction.shape}, Accuracy:{accuracy}")  
        # Compute overall validation accuracy
        gridValidationAcc = np.mean(nFoldValidAcc)
        gridValidationsOuputs[c] = {
            "accuracy": gridValidationAcc,
            "predictions": Prediction,
            "knowns": Known
        }
        print(f"Value C: {c}, Average Accuracy:{gridValidationAcc}")
    
    # Create a plot with Accuracies and C values
    allAccuracies = [gridValidationsOuputs[k]['accuracy'] for k in gridValidationsOuputs.keys()]
    plt.figure(figsize=(16, 14), facecolor='white')
    plt.plot(param_grid['C'], allAccuracies, marker='o', markersize=5, color='blue')
    plt.title('Validation Accuracy vs. C', fontsize=20, color='darkblue')
    plt.xlabel('C', fontsize=18)
    plt.ylabel('Validation Accuracy', fontsize=18)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.grid()
    plt.show()

    # find the key with maximum value for all accuracy in dictionary gridValidationAcc
    bestC = max(gridValidationsOuputs, key=lambda k: gridValidationsOuputs[k]['accuracy'])
    validationAccuracy = gridValidationsOuputs[bestC]['accuracy']

    # Train classifier using training dataset
    clf = svm.SVC(kernel='rbf', gamma='auto', C=bestC) #--> Validation SVM object
    if ClassLabels.shape[0] == 6:
        # In case you have 6 unique labels, assign weights to each class
        prior_dict ={ClassLabels[0]: 0.5, ClassLabels[1]: 6.67, ClassLabels[2]: 50, 
                    ClassLabels[3]: 3.22, ClassLabels[4]: 3.33, ClassLabels[5]: 33.3} #--> Prior weights
        clf.set_params(class_weight = prior_dict) #--> Add prior weights parameter
        # CVclf.set_params(class_weight="balanced")
        # Fit data
        clf.fit(predictors, response)
    else:
        # In case you have more (or less) than 6 unique labels, fit right away
        clf.set_params(class_weight="balanced")
        clf.fit(predictors, response)
    

    # Compute the confusion matrix
    C = metrics.confusion_matrix(gridValidationsOuputs[bestC]['knowns'], gridValidationsOuputs[bestC]['predictions'])

    # Plot confusion matrix
    conf_val = pd.DataFrame(C)
    plt.figure(figsize = (16,14),facecolor='white')
    heatmap = sns.heatmap(conf_val, annot = True, annot_kws = {'size': 20}, fmt = 'd', cmap = 'YlGnBu')
    heatmap.yaxis.set_ticklabels(label, rotation = 0, ha = 'right', fontsize = 18, weight='bold')
    heatmap.xaxis.set_ticklabels(label, rotation = 0, ha = 'right', fontsize = 18, weight='bold')
    plt.title('Validation Confusion Matrix\n', fontsize = 18, color = 'darkblue')
    plt.ylabel('True label', fontsize = 14)
    plt.xlabel('Predicted label', fontsize = 14)
    plt.show()
    
    return clf, validationAccuracy, C

def Predict(clf, predictors):
    """
    Returns predictions made by a classifier object.

    Parameters
    ----------
    predictors : numpy array of float64
        A 1D array containing features.
    clf: SVC object of sklearn.svm._classes module
        A classifier object that can be used to predict activities.

    Returns
    -------
    pred : numpy array of float64
        A 1D array containing predictions.

    """
    predictors = preprocessing.scale(predictors) #--> Standardize features
    pred = clf.predict(predictors) #--> Get predictions using classifier object
    return pred