# -*- coding: utf-8 -*-
"""

Created on Fri Sep 18 22:12:37 2020

@author: Evgeny V. Votyakov aka karaul, karaul@gmail.com, Cyprus, Nicosia

example:
del tkldataframe, tklf
import tkldataframe as tkldf
filename = 'D:/GoogleDrive/RUN/DataGPSMaster12/karaul/2012/11/20121103200009.tkl'
df=tkldf.read_file(filename)
# print(df)
print(df['HR'])
print(df['speed'])
print(df['HRE'])


Parse record byte array and return dictionary containing latitude, longitude, date and altitude
Based on Robware answer on 
https://www.reddit.com/r/ukbike/comments/29i7nt/did_anyone_else_get_the_gps_watch_from_the_aldi/
https://www.reddit.com/r/ukbike/comments/29i7nt/did_anyone_else_get_the_gps_watch_from_the_aldi/cilkru4/
(changed long/lat, numbering starts from 0)
GPS Data (32 bytes):
00|01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31
-----------------------------------------------------------------------------------------------
  |  |Y |M |D |H |m |S | Long      | Lat       |Alt  | Head|Speed|Dist |HR|  |  |  |  |  |  |

Speed is measured in Metres per hour
Distance is measured in cm and it is distance from the previous point


I can extract all the GPS and heart rate information from the file so far, excluding the satellite count.

I first tried a hex editor, but that wasn't giving me anything useful, other than showing a repeating pattern to the
data after a certain point.
I then just made myself a simple C# console app that loaded in the file and printed out the byte data.
From there the pattern became clearer, and I started a trial and error approach of reading various data types.
I had the software open on my other monitor so I could read the values it got. First I got the lat and long, then once
I got the altitude and heart rate I started to fill the gaps much quicker.

Here's what I have from a couple of evenings at it:

Header (256 bytes?):
	192: int GPS record count (is this a short or int?)
	210: lap count?
	211-216: start timestamp
	217-219: total workout time?
	274-279: timestamp
	228-229: avg speed?
	230-231: max speed?
	236: average heart rate?
	237: max heart rate?
	238: min heart rate?
	244-246: hr below zone time?
	248-250: hr in zone time?
	252-254: hr above zone time?

Lap data (16 bytes?):
01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16
-----------------------------------------------
  |  |  |  |  |  |  |  |  |  |  |  |AS|  |  |

AS=Average Speed

GPS Data (32 bytes):
01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31|32
-----------------------------------------------------------------------------------------------
  |  |Y |M |D |H |m |S | Lat       | Long      |Alt  | Head|Speed|Dist |HR|  |  |  |  |  |  |

First 2 bytes are something to do with GPS signal/number of satelites.
Speed is measured in Metres per hour
Distance is measured in cm and is distance from previous point

"""

import os
import argparse
import easygui
import binascii
from dateutil.parser import parse
import struct
import codecs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
import webbrowser


def parse_record(bytes):
    res = {}
    #timestamp 3->8
    b25_bytes=map(lambda b: str(b).zfill(2),bytes[2:5])
    b58_bytes=map(lambda b: str(b).zfill(2),bytes[5:8])
    datebody="-".join(b25_bytes) + "T" + ":".join(b58_bytes)
    res['date'] = parse("20"+ datebody  +"Z")
    
    #longtitude	8->11
    lon_bytes = bytes[8:12][::-1] #reverse bytes
    res['lon'] = struct.unpack('>i',codecs.decode(binascii.hexlify(bytearray(lon_bytes)),'hex'))[0]/10000000.0
    #latitude 12->15
    lat_bytes =  bytes[12:16][::-1]	#reverse bytes	
    res['lat'] = struct.unpack('>i',codecs.decode(binascii.hexlify(bytearray(lat_bytes)),'hex'))[0]/10000000.0
    
    #altitude 16->17
    alt_bytes =  bytes[16:18][::-1] #reverse bytes
    res['alt'] = float(int(binascii.hexlify(bytearray(alt_bytes)),16))
    
    dist_bytes =  bytes[22:24][::-1] #reverse bytes, sm, it is the distance form the previous point
    res['dist'] = float(int(binascii.hexlify(bytearray(dist_bytes)),16))/10

    speed_bytes =  bytes[20:22][::-1] #reverse bytes, sm/hour
    res['speed'] = float(int(binascii.hexlify(bytearray(speed_bytes)),16))/100
    
    hr_bytes =  bytes[24:25][::-1] #reverse bytes
    res['HR'] = float(int(binascii.hexlify(bytearray(hr_bytes)),16))
    
    return res

def read_file(filename):
    # filename = 'D:/GoogleDrive/RUN/DataGPSMaster12/karaul/2012/11/20121103200009.tkl'
    try:
        f = open(filename, "rb")
        f.seek(210) #skip to lap count
        lap_count = ord(f.read(1))
        f.seek(256 + lap_count * 16) #skip header + lap data * count
        #each record is 32 bytes
        bytes = f.read(32) 
        ar = []
        while len(bytes)==32:
            dct = parse_record(bytes)
            ar.append(dct)
            bytes = f.read(32)
    except:
        print('Could not read: ', filename)
        print('Priobably, it is not tkl format')
    finally:
        f.close()
        
    # df=pd.DataFrame(ar)
    # df=df.transpose()
    df=pd.DataFrame(ar).to_dict('series')
    
    df['dist']=np.cumsum(df['dist'])
    df['pace'] = 60/df['speed']
    df['pace']=df['pace'].replace([np.inf, -np.inf], np.nan)
    df['HRE'] = df['HR']*df['pace']
    return df

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", help="tkl file name")
    args = parser.parse_args()
    filename=args.filename
    if not filename:
        filename=easygui.fileopenbox()

    df=read_file(filename)
    plotlabel=os.path.basename(filename)[:8]
    plt.figure(1)
    ax1=plt.subplot(311)
    param='pace'
    ylimmean=df[param].mean()
    ax1.plot(df['dist']/1000,df[param], \
             label=plotlabel+'  mean: '+f"{ylimmean:5.2f}")
    #plt.ylim([3,7])
    plt.ylim([ylimmean*0.8,ylimmean*1.2])
    plt.grid(True)
    plt.title(param) 
    plt.legend()
    
    ax2=plt.subplot(312)
    param='HR'
    ylimmean=df[param].mean()
    ax2.plot(df['dist']/1000,df[param], \
             label=plotlabel+'  mean: '+f"{ylimmean:4.0f}")
    #plt.ylim([3,7])
    plt.ylim([ylimmean*0.8,ylimmean*1.2])
    plt.grid(True)
    plt.title(param) 
    plt.legend()
    
    ax3=plt.subplot(313)
    param='HRE'
    ylimmean=df[param].mean()
    ax3.plot(df['dist']/1000,df[param], \
             label=plotlabel+'  mean: '+f"{ylimmean:4.0f}")
    #plt.ylim([3,7])
    plt.ylim([ylimmean*0.8,ylimmean*1.2])
    plt.grid(True)
    plt.title(param) 
    plt.legend()
    
    plt.tight_layout()

    # track on the map
    dfpos=pd.DataFrame.from_dict(zip(df['lat'], df['lon'])).dropna()
    #dfnonan=df.dropna(subset = ['position_lat', 'position_long'])
    #dfnonan=dfpos
    map_track=folium.Map(dfpos.mean().values.tolist())
    map_track.fit_bounds([dfpos.min().values.tolist(), dfpos.max().values.tolist()]) 
    folium.PolyLine(zip(dfpos[0], dfpos[1]),color="blue", weight=2.5, opacity=1).add_to(map_track)

    # Save map
    filenamehtml=os.path.join(os.getcwd(), os.path.basename(filename))
    filenamehtml=filenamehtml[:-3]+'html'
    map_track.save(filenamehtml)
    # open an HTML file on my own (Windows) computer
    url = 'file://' + os.path.realpath(filenamehtml)
    webbrowser.open(url,new=2)