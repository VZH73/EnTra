# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 13:13:22 2020

@author: karaul

How to backup all your activities from garmin connect

- install garminexport
https://pypi.org/project/garminexport/
read garminexport documnetation. They have CLI with few commands, to backup 
all activities use garmin-backup

- start powershell from anaconda, type in the prompt 
garmin-backup.exe --password PASSWORD -f fit USER_ACCOUNT
USER_ACCOUNT - Garmin account
PASSWORD - Garmin password

"""

# import sys
import os
from pathlib import Path

import argparse
# import easygui
from fitparse import FitFile
# import fitdataframe as fitdf
from tkldataframe import read_file as read_file_tkl
import pandas as pd
# import matplotlib.pyplot as plt
# import numpy as np
import time
# import tkinter as tk
# from tkinter import *
# import tkinter as tk                     
# from tkinter import ttk 
# from pandastable import Table, TableModel

def read_file(filename, check_fitfile):
    
    fitfile = FitFile(filename)
    
    if check_fitfile:
        while True:
            try:
                fitfile.messages
                break
            except KeyError:
                continue
        
    workout = {}
    # workout['filename'] = os.path.basename(filename)
    needed_names=['time_created','sport','sub_sport', 
       'total_timer_time', 'total_distance',
       'avg_heart_rate','avg_running_cadence', 'total_elapsed_time',
       'enhanced_avg_speed']
    message_names=['file_id', 'sport', 'activity', 'session']
    
    for message_name in  message_names:
        for record in fitfile.get_messages(message_name):
            for data in record:
                if data.name in needed_names:
                    # print(data.name)
                    workout[data.name] = data.value
                    needed_names.remove(data.name)
    
    if 'total_distance' in workout:                
        workout['total_distance'] =  workout['total_distance']/1000    

    if 'total_timer_time' in workout:                
        n= workout['total_timer_time']
        workout['total_timer_time'] = time.strftime("%H:%M:%S", time.gmtime(n))
        
    checknames= ('enhanced_avg_speed','avg_heart_rate')    
    if set(checknames).issubset(workout):
        if not(workout['enhanced_avg_speed']==None or 
               workout['avg_heart_rate']==None):
            workout['avg_pace'] = 1/(60*workout[ 'enhanced_avg_speed']/1000)
            workout['avg_HRE'] = workout['avg_pace']*workout['avg_heart_rate']

    if 'total_elapsed_time' in workout:                
        n= workout['total_elapsed_time']
        workout['total_elapsed_time'] = time.strftime("%H:%M:%S", time.gmtime(n))

    workout['filename'] = filename

    return workout

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", help="workouts csv file")
    args = parser.parse_args()
    filename_csv=args.filename
    # if not filename_csv:
    #     # filename_csv=easygui.fileopenbox()
    #     filename_csv='./workouts2020-08-fit.csv'

    if filename_csv:
        workouts = pd.read_csv(filename_csv)
    else:
        
        # filename_csv='t.csv'
        actvity_folder='./activities/'
        filename_mask = '2020*.fit'
        #--- treat tkl files
        # actvity_folder='../../DataGPSMaster12/karaul/'
        # filename_mask ='2016/*/*.tkl'
        # filename_mask ='2012/11/*.tkl'
        
        #filenamesfull = list(Path(actvity_folder).glob(filename_mask))
        filenamesfull = []
        for filename in sorted(list(Path(actvity_folder).glob(filename_mask)), 
            key = lambda file: os.path.getctime(file), reverse=True):
            if (time.time() - os.path.getctime(filename) > 0.5*(3600*24)) :
                break
            filenamesfull.append(filename)        
        
        filename_csv=actvity_folder+( filename_mask).\
          replace('*', '').replace('.', '-').replace('/', '-') + \
          '.csv' #[:-4] #+'-fit.csv'
        
        # (_, _, filenames) = next(os.walk('./activities'))
            
        try:
            workouts = pd.read_csv(filename_csv)
            filenames=[]
            for filename in filenamesfull:
                if (str(filename) not in workouts['filename'].values):
                    filenames.append(filename)
        except IOError:
            workouts = pd.DataFrame()
            filenames = filenamesfull
            
        check_fitfile = True #False


        for i in range(len(filenames)):
            
            filename=str(filenames[i])
            print( str(i) + ' out of '+ str(len(filenames)) )
            
            if filename[-4:] == '.fit':
                workout = read_file(filename, check_fitfile)
            elif filename[-4:] == '.tkl':
                df = read_file_tkl(filename)
                workout = {}
                workout['time_created'] = str(df['date'].tail(1).item()).replace('+00:00','')
                workout['sport'] = 'running'
                tottime=df['date'].tail(1).item() - df['date'].head(1).item()
                workout['total_distance'] = df['dist'].tail(1).item()/1000
                workout['total_elapsed_time'] = str(tottime).replace('0 days ','')
                #workout['avg_pace'] = df['pace'].mean()
                workout['avg_pace'] = (tottime.total_seconds())/60/workout['total_distance']
                workout['avg_heart_rate'] = df['HR'].mean()
                workout['avg_HRE'] = workout['avg_pace']*workout['avg_heart_rate']
                workout['filename'] = filename
                # Some comments
            
            workouts=workouts.append(workout, ignore_index=True)

        workouts.to_csv(filename_csv, index = False)
        
    print(workouts)
    # print('done')
    

