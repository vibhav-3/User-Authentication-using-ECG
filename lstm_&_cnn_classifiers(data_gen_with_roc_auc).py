# -*- coding: utf-8 -*-
"""LSTM & CNN classifiers(data_gen with ROC AUC).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1yINFVZUa8wjwsvmBg9M-Z-dfUj-HYLyx
"""

from google.colab import drive
drive.mount('/content/gdrive')

PATH='/content/gdrive/MyDrive/Colab Notebooks/ecg-id-database-1.0.0'

!pip install wfdb
!pip install progress

import os
import random
import itertools
import wfdb
from wfdb import processing
import numpy as np
import pandas as pd
from progress.bar import Bar
import heapq
from scipy.stats.stats import pearsonr

def dataGeneration(data_path, csv_path, record_path):

    # initialize dataset
    dataset = pd.DataFrame(columns=['label', 'record'])

    if record_path == None:

        # a loop for each patient
        detail_path = data_path + '/'
        record_files = [i.split('.')[0] for i in os.listdir(detail_path) if (not i.startswith('.') and i.endswith('.hea'))]

        Bar.check_tty = False
        bar = Bar('Processing', max=len(record_files), fill='#', suffix='%(percent)d%%')

        # a loop for each record
        for record_name in record_files:

            # load record
            signal, info = wfdb.rdsamp(detail_path + record_name)

            fs = 200

            signal = processing.resample_sig(signal[:,0], info['fs'], fs)[0]

            # set some parameters
            window_size_half = int(fs * 0.125 / 2)
            max_bpm = 230

            # detect QRS peaks
            qrs_inds = processing.gqrs_detect(signal, fs=fs)
            search_radius = int(fs*60/max_bpm)
            corrected_qrs_inds = processing.correct_peaks(signal, peak_inds=qrs_inds, search_radius=search_radius, smooth_window_size=150)

            average_qrs = 0
            count = 0
            for i in range(1, len(corrected_qrs_inds)-1):
                start_ind = corrected_qrs_inds[i] - window_size_half
                end_ind = corrected_qrs_inds[i] + window_size_half + 1
                if start_ind<corrected_qrs_inds[i-1] or end_ind>corrected_qrs_inds[i+1]:
                    continue
                average_qrs = average_qrs + signal[start_ind: end_ind]
                count = count + 1

            # remove outliers
            if count < 8:
                print('\noutlier detected, discard ' + record_name)
                continue

            average_qrs = average_qrs / count

            corrcoefs = []
            for i in range(1, len(corrected_qrs_inds)-1):
                start_ind = corrected_qrs_inds[i] - window_size_half
                end_ind = corrected_qrs_inds[i] + window_size_half + 1
                if start_ind<corrected_qrs_inds[i-1] or end_ind>corrected_qrs_inds[i+1]:
                    corrcoefs.append(-100)
                    continue
                corrcoef = pearsonr(signal[start_ind: end_ind], average_qrs)[0]
                corrcoefs.append(corrcoef)

            max_corr = list(map(corrcoefs.index, heapq.nlargest(8, corrcoefs)))

            index_corr = random.sample(list(itertools.permutations(max_corr, 8)), 100)

            for index in index_corr:
                # a temp dataframe to store one record
                record_temp = pd.DataFrame()

                signal_temp = []

                for i in index:
                    start_ind = corrected_qrs_inds[i + 1] - window_size_half
                    end_ind = corrected_qrs_inds[i + 1] + window_size_half + 1
                    sig = processing.normalize_bound(signal[start_ind: end_ind], -1, 1)
                    signal_temp = np.concatenate((signal_temp, sig))

                record_temp = record_temp.append(pd.DataFrame(signal_temp.reshape(-1,signal_temp.shape[0])), ignore_index=True, sort=False)
                record_temp['label'] = record_name
                record_temp['record'] = record_name

                # add it to final dataset
                dataset = dataset.append(record_temp, ignore_index=True, sort=False)
                
            bar.next()    
        bar.finish()    
    else:
        patient_folders = [i for i in os.listdir(data_path) if (not i.startswith('.') and i.startswith(record_path))]

        print(data_path, ' - ',record_path)

        Bar.check_tty = False
        bar = Bar('Processing', max=len(patient_folders), fill='#', suffix='%(percent)d%%')
        # a loop for each patient
        print(len(patient_folders))
        for patient_name in patient_folders:
            detail_path = data_path + patient_name + '/'
            record_files = [i.split('.')[0] for i in os.listdir(detail_path) if i.endswith('.hea')]

            # a loop for each record
            for record_name in record_files:

                # load record
                signal, info = wfdb.rdsamp(detail_path + record_name)

                fs = 200

                signal = processing.resample_sig(signal[:,0], info['fs'], fs)[0]

                # set some parameters
                window_size_half = int(fs * 0.125 / 2)
                max_bpm = 230

                # detect QRS peaks
                qrs_inds = processing.gqrs_detect(signal, fs=fs)
                search_radius = int(fs*60/max_bpm)
                corrected_qrs_inds = processing.correct_peaks(signal, peak_inds=qrs_inds, search_radius=search_radius, smooth_window_size=150)

                average_qrs = 0
                count = 0
                for i in range(1, len(corrected_qrs_inds)-1):
                    start_ind = corrected_qrs_inds[i] - window_size_half
                    end_ind = corrected_qrs_inds[i] + window_size_half + 1
                    if start_ind<corrected_qrs_inds[i-1] or end_ind>corrected_qrs_inds[i+1]:
                        continue
                    average_qrs = average_qrs + signal[start_ind: end_ind]
                    count = count + 1

                # remove outliers
                if count < 8:
                    print('\noutlier detected, discard ' + record_name + ' of ' + patient_name)
                    continue

                average_qrs = average_qrs / count

                corrcoefs = []
                for i in range(1, len(corrected_qrs_inds)-1):
                    start_ind = corrected_qrs_inds[i] - window_size_half
                    end_ind = corrected_qrs_inds[i] + window_size_half + 1
                    if start_ind<corrected_qrs_inds[i-1] or end_ind>corrected_qrs_inds[i+1]:
                        corrcoefs.append(-100)
                        continue
                    corrcoef = pearsonr(signal[start_ind: end_ind], average_qrs)[0]
                    corrcoefs.append(corrcoef)

                max_corr = list(map(corrcoefs.index, heapq.nlargest(8, corrcoefs)))

                index_corr = random.sample(list(itertools.permutations(max_corr, 8)), 100)

                for index in index_corr:
                    # a temp dataframe to store one record
                    record_temp = pd.DataFrame()

                    signal_temp = []

                    for i in index:
                        start_ind = corrected_qrs_inds[i + 1] - window_size_half
                        end_ind = corrected_qrs_inds[i + 1] + window_size_half + 1
                        sig = processing.normalize_bound(signal[start_ind: end_ind], -1, 1)
                        signal_temp = np.concatenate((signal_temp, sig))

                    record_temp = record_temp.append(pd.DataFrame(signal_temp.reshape(-1,signal_temp.shape[0])), ignore_index=True, sort=False)
                    record_temp['label'] = patient_name
                    record_temp['record'] = record_name

                    # add it to final dataset
                    dataset = dataset.append(record_temp, ignore_index=True, sort=False)
                
            bar.next()    
        bar.finish()

    # save for further use
    print(csv_path)
    dataset.to_csv(f'{PATH}/{csv_path}', index=False)

    print('processing completed')


dataset_name = PATH
record_path = 'Person'#'patient'
# root path
data_path = dataset_name + '/'

csv_path = 'ptb.csv'

dataGeneration(data_path, csv_path, record_path)

"""# CNN"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import keras
import keras.backend as K
from keras import Model
from keras.models import Sequential
from keras.layers import Input, Softmax, Conv1D, Dense, Dropout, ReLU, MaxPooling1D, Flatten
# from keras.optimizers import Adam
from keras.callbacks import LearningRateScheduler
from keras.utils import np_utils
from keras.callbacks import ModelCheckpoint

import sklearn
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from sklearn import metrics
import pickle



#preprocessor ptb

dataset = pd.read_csv("/content/gdrive/MyDrive/Colab Notebooks/ecg-id-database-1.0.0/ptb.csv")
x_cols = [col for col in dataset.columns if (col != 'label' and col != 'record')]
X_data = dataset[x_cols].values
X_data = np.reshape(X_data, (X_data.shape[0], X_data.shape[1], -1))
Y_data = dataset['label'].values
X_train, X_test, Y_train, Y_test = train_test_split(X_data, Y_data, random_state=0, test_size = 0.3, train_size = 0.7)


num_classes = len(np.unique(Y_data))

print(num_classes,Y_train.shape,X_train.shape)
Y_train_encoder = sklearn.preprocessing.LabelEncoder()
Y_train_num = Y_train_encoder.fit_transform(Y_train)
Y_train_wide = np_utils.to_categorical(Y_train_num, num_classes)

Y_test_num = Y_train_encoder.fit_transform(Y_test)
Y_test_wide = np_utils.to_categorical(Y_test_num, num_classes)

#model cnn
input_shape = (X_train.shape[1], X_train.shape[2])
#print(input_shape)
inputs = Input(shape=input_shape)
x = Conv1D(16, 7)(inputs)
x = ReLU()(x)
x = MaxPooling1D(pool_size=3, strides=2)(x)

x = Conv1D(32 ,5)(x)
x = ReLU()(x)
x = MaxPooling1D(pool_size=3, strides=2)(x)

x = Conv1D(64, 5)(x)
x = ReLU()(x)
x = MaxPooling1D(pool_size=3, strides=2)(x)

x = Conv1D(128, 7)(x)
x = ReLU()(x)

x = Conv1D(256, 7)(x)
x = ReLU()(x)

x = Conv1D(256, 8)(x)
x = ReLU()(x)
x = Dropout(0.5)(x)

x = Flatten()(x)
x = Dense(num_classes)(x)

predictions = Softmax()(x)

cnn_model = Model(inputs=inputs, outputs=predictions)

cnn_model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])
cnn_model.summary()

# training
batch_size = 16
epochs = 20

# set up the callback to save the best model based on validaion data
best_weights_filepath = './best_weights.hdf5'
mcp = ModelCheckpoint(best_weights_filepath, monitor="val_accuracy",
                    save_best_only=True, save_weights_only=False)

history = cnn_model.fit(X_train, Y_train_wide,
            batch_size=batch_size,
            epochs=epochs,
            verbose = 1,
            validation_split = 0.2,
            shuffle=True,
            callbacks=[mcp])

cnn_model.load_weights(best_weights_filepath)

    # save model
cnn_model.save('cnn_model.h5')

loss = history.history['loss']
val_loss = history.history['val_loss']
accuracy = history.history['accuracy']
val_accuracy= history.history['val_accuracy']

plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.plot(loss, 'blue', label='Training Loss')
plt.plot(val_loss, 'green', label='Validation Loss')
plt.xticks(range(0,epochs)[0::2])
plt.legend()
plt.show()
plt.xlabel('Epochs')
plt.ylabel('accuracy')
plt.plot(accuracy, 'blue', label='Training accuracy')
plt.plot(val_accuracy, 'green', label='Validation accuracy')
plt.xticks(range(0,epochs)[0::2])
plt.legend()
plt.show()

cnn_pred = np.argmax(cnn_model.predict(X_test), axis=-1)

# print performance details
print(metrics.classification_report(Y_test_num, cnn_pred))

THRESHOLD_CNN = 0.5
LINE_CNN = 1

# Get the index of the highest probability

cut = X_test[LINE_CNN][0:90]
prob_lstm = cut[cut>THRESHOLD_CNN]
INDEX_CNN  =np.where(X_test[LINE_CNN][0:90]==prob_lstm[0])[0]
INDEX_CNN



# Get the patient:

input= X_test[INDEX_CNN[0]]
input = np.expand_dims(input, axis=0)
Y_pred = cnn_model.predict(input)
print('User No: ' + str(np.argmax(Y_pred,axis=1)))

import matplotlib.pyplot as plt 
from sklearn.preprocessing import LabelBinarizer
from sklearn.metrics import roc_curve, auc, roc_auc_score


target = np.unique(Y_data)


# set plot figure size
fig, c_ax = plt.subplots(1,1, figsize = (12, 8))

# function for scoring roc auc score for multi-class
def multiclass_roc_auc_score_cnn(y_test, y_pred, average="macro"):
    lb = LabelBinarizer()
    lb.fit(y_test)
    y_test = lb.transform(y_test)
    y_pred = lb.transform(y_pred)
    fpr, tpr=0,0
    for (idx, c_label) in enumerate(target):
        fpr, tpr, thresholds = roc_curve(y_test[:,idx].astype(int), y_pred[:,idx])
        #c_ax.plot(fpr, tpr, label = '%s (AUC:%0.2f)'  % (c_label, auc(fpr, tpr)))
        c_ax.plot(fpr, tpr)
    c_ax.plot(fpr, tpr, label = 'Person 0 to 90 (AUC 1.00)')    
    c_ax.plot(fpr, fpr, 'b-', label = 'Random Guessing')
    return roc_auc_score(y_test, y_pred, average=average)

    
print('ROC AUC score:', multiclass_roc_auc_score_cnn(Y_test_num, cnn_pred))

c_ax.legend()
c_ax.set_title('CNN')
c_ax.set_xlabel('False Positive Rate')
c_ax.set_ylabel('True Positive Rate')
plt.show()

"""# LSTM"""



from keras.layers import Dense, Dropout, LSTM, Embedding,Flatten
#from keras.preprocessing.sequence import pad_sequences
from keras.models import Sequential
import tensorflow as tf
from keras.callbacks import EarlyStopping

lstm_model = Sequential()
lstm_model.add(LSTM(32, input_shape = input_shape , return_sequences=True))
lstm_model.add(Dropout(0.2))
lstm_model.add(LSTM(32, return_sequences=True))
lstm_model.add(Dropout(0.1))
lstm_model.add(Flatten())
lstm_model.add(Dense(num_classes, activation='Softmax'))
opt = tf.keras.optimizers.Adam(learning_rate=0.001)

callback = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=3)

lstm_model.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy'])
history = lstm_model.fit(X_train, Y_train_wide, validation_split=0.1, epochs=20, shuffle=True)#, callbacks=[callback])


plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()


plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()


lstm_pred = np.argmax(lstm_model.predict(X_test), axis=-1)

# print performance details
print(metrics.classification_report(Y_test_num, lstm_pred))

THRESHOLD_LSTM = 0.65
LINE_LSTM = 1

# Get the index of the highest probability

cut = X_test[LINE_LSTM][0:90]
prob_lstm = cut[cut>THRESHOLD_LSTM]
INDEX_LSTM  =np.where(X_test[LINE_LSTM][0:90]==prob_lstm[0])[0]
print(INDEX_LSTM)



# Get the patient:

input= X_test[INDEX_LSTM[0]]
input = np.expand_dims(input, axis=0)
Y_pred = lstm_model.predict(input)
print('User No: ' + str(np.argmax(Y_pred,axis=1)))

from sklearn.metrics import roc_curve, auc
from sklearn import datasets
from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import LinearSVC
from sklearn.preprocessing import label_binarize
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns

np.unique(Y_data)

import matplotlib.pyplot as plt 
from sklearn.preprocessing import LabelBinarizer
from sklearn.metrics import roc_curve, auc, roc_auc_score


#target= ['airplane', 'automobile', 'bird', 'cat', 'deer','dog', 'frog', 'horse', 'ship', 'truck']

target = np.unique(Y_data)


# set plot figure size
fig, c_ax = plt.subplots(1,1, figsize = (12, 8))

# function for scoring roc auc score for multi-class
def multiclass_roc_auc_score(y_test, y_pred, average="macro"):
    lb = LabelBinarizer()
    lb.fit(y_test)
    y_test = lb.transform(y_test)
    y_pred = lb.transform(y_pred)
    fpr, tpr=0,0
    for (idx, c_label) in enumerate(target):
        fpr, tpr, thresholds = roc_curve(y_test[:,idx].astype(int), y_pred[:,idx])
        #c_ax.plot(fpr, tpr, label = '%s (AUC:%0.2f)'  % (c_label, auc(fpr, tpr)))
        c_ax.plot(fpr, tpr)
    c_ax.plot(fpr, tpr, label = 'Person 0 to 90 (AUC 1.00)')    
    c_ax.plot(fpr, fpr, 'b-', label = 'Random Guessing')
    return roc_auc_score(y_test, y_pred, average=average)

    
print('ROC AUC score:', multiclass_roc_auc_score(Y_test_num, lstm_pred))

c_ax.legend()
c_ax.set_title('LSTM')
c_ax.set_xlabel('False Positive Rate')
c_ax.set_ylabel('True Positive Rate')
plt.show()

Y_test_num.shape, lstm_pred.shape,Y_data.shape

