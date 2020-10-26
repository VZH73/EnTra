# -*- coding: utf-8 -*-
"""

Created on Fri Sep 18 22:12:37 2020

@author: Evgeny V. Votyakov aka karaul, karaul@gmail.com, Cyprus, Nicosia

example:
import fitdataframe as fitdf
filename = './activities/2020-09-11T16_06_08+00_00_5521461232.fit'
df=fitdf.read_file(filename)
print(df)

"""

import os
import argparse
#import sys
import easygui
# from easygui import fileopenbox
from fitparse import FitFile
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import folium
import webbrowser


def read_file(filename):
    #fname='./activities/2020-09-11T16_06_08+00_00_5521461232.fit'
    fitfile = FitFile(filename)
    
    # This is a ugly hack
    # to avoid timing issues
    while True:
        try:
            fitfile.messages
            break
        except KeyError:
            continue

    # Get all data messages that are of type record
    workout = []
    for record in fitfile.get_messages('record'):
        r = {}
        # Go through all the data entries in this record
        for record_data in record:
            r[record_data.name] = record_data.value
        workout.append(r)

    df = pd.DataFrame(workout)

    if set(['enhanced_speed','heart_rate']).issubset(df.columns):
        df['pace']=1/(60*df[ 'enhanced_speed']/1000)
        df['pace']=df['pace'].replace([np.inf, -np.inf], np.nan)
        df['HRE']=df['pace']*df['heart_rate']

    if set(['position_lat','position_long']).issubset(df.columns):
        df['position_lat']=df['position_lat']*180/2**31
        df['position_long']=df['position_long']*180/2**31

    return df

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", help="fit file name")
    args = parser.parse_args()
    filename=args.filename
    if not filename:
        filename=easygui.fileopenbox()

    df=read_file(filename)
    
    plotlabel=os.path.basename(filename)[:10]
    # plotlabel=fitfile.messages[0].get_value('time_created').strftime('%Y-%m-%d')
    
    # plt.figure(1)
    # ax1=plt.subplot(311)
    # param='pace'
    # ylimmean=df[param].mean()
    # ax1.plot(df['distance']/1000,df[param], \
    #          label=plotlabel+'  mean: '+f"{ylimmean:5.2f}")
    # #plt.ylim([3,7])
    # plt.ylim([ylimmean*0.8,ylimmean*1.2])
    # plt.grid(True)
    # plt.title(param) 
    # plt.legend()
    
    # ax2=plt.subplot(312)
    # param='heart_rate'
    # ylimmean=df[param].mean()
    # ax2.plot(df['distance']/1000,df[param], \
    #          label=plotlabel+'  mean: '+f"{ylimmean:4.0f}")
    # #plt.ylim([3,7])
    # plt.ylim([ylimmean*0.8,ylimmean*1.2])
    # plt.grid(True)
    # plt.title(param) 
    # plt.legend()
    
    # ax3=plt.subplot(313)
    # param='HRE'
    # ylimmean=df[param].mean()
    # ax3.plot(df['distance']/1000,df[param], \
    #          label=plotlabel+'  mean: '+f"{ylimmean:4.0f}")
    # #plt.ylim([3,7])
    # plt.ylim([ylimmean*0.8,ylimmean*1.2])
    # plt.grid(True)
    # plt.title(param) 
    # plt.legend()
    
    # plt.tight_layout()
    
    fig, ax1 = plt.subplots(dpi=100)

    param='heart_rate'
    color = 'tab:red'
    ax1.set_xlabel('distance (km)')
    ax1.set_ylabel(param, color=color)
    ylimmean=df[param].mean()
    ax1.plot(df['distance']/1000,df[param], color=color,
              label=plotlabel+'  mean: '+f"{ylimmean:5.2f}")
    #plt.ylim([3,7])
    ax1.set_ylim([ylimmean*0.8,ylimmean*1.2])
    ax1.grid(True,color=color,linestyle='--')
    # plt.title(param) 
    # plt.legend()
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    
    param='pace'
    color = 'tab:blue'
    ax2.set_ylabel(param, color=color)  # we already handled the x-label with ax1
    ylimmean=df[param].mean()
    ax2.plot(df['distance']/1000,df[param], color=color,
              label=plotlabel+'  mean: '+f"{ylimmean:5.2f}")
    #plt.ylim([3,7])
    ax2.set_ylim([ylimmean*0.8,ylimmean*1.2])
    ax2.grid(True,color=color,linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color)
    
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()
    
    if set(['cadence']).issubset(df.columns):
        plt.figure(2)
        param='cadence'
        ylimmean=2*df[param].mean()
        plt.plot(df['distance']/1000,2*df[param], \
                 label=plotlabel+'  mean: '+f"{ylimmean:3.0f}")
        plt.ylim([ylimmean*0.9,ylimmean*1.1])
        plt.grid(True)
        plt.title(param) 
        plt.legend()
        
        plt.show()

    # track on the map
    dfpos=df[['position_lat', 'position_long']]. \
                dropna(subset = ['position_lat', 'position_long']). \
                rename(columns={'position_lat': 0, 'position_long': 1})
    #dfnonan=df.dropna(subset = ['position_lat', 'position_long'])
    #dfnonan=dfpos
    map_track=folium.Map(dfpos.mean().values.tolist())
    map_track.fit_bounds([dfpos.min().values.tolist(), dfpos.max().values.tolist()]) 
    folium.PolyLine(zip(dfpos[0], dfpos[1]), color="blue", weight=2.5, opacity=1).add_to(map_track)

    # Save map
    filenamehtml=os.path.join(os.getcwd(), os.path.basename(filename))
    filenamehtml=filenamehtml[:-3]+'html'
    map_track.save(filenamehtml)
    # open an HTML file on my own (Windows) computer
    url = 'file://' + os.path.realpath(filenamehtml)
    webbrowser.open(url,new=2)