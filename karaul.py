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

import os
import argparse
import easygui

import tkinter as tk
from tkinter import ttk
import pandas as pd
from pandastable import Table, TableModel
import fitdataframe as fitdf
import tkldataframe as tkldf
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import numpy as np
import folium
import webbrowser

class App(tk.Tk):
    
    def __init__(self, filename_wrk):

        tk.Tk.__init__(self)
        self.geometry("800x600")
        self.title("Main Window: "+ filename_wrk)
        
        menubar  = tk.Menu(self)
        self.config(menu=menubar)
        activitiesmenu = tk.Menu(menubar)
        menubar.add_cascade(label="Activities", menu=activitiesmenu)
        activitiesmenu.add_command(label="Open", command=self.menuopen)
        activitiesmenu.add_command(label="New")#, command=NewFile)
        activitiesmenu.add_command(label="Save")#, command=OpenFile)
        activitiesmenu.add_separator()
        activitiesmenu.add_command(label="Exit", command=self.menuquit)
        
        workoutmenu = tk.Menu(menubar)
        menubar.add_cascade(label="Workout", menu=workoutmenu)
        workoutmenu.add_command(label="Track", command=self.show_track)
        workoutmenu.add_separator()
        workoutmenu.add_command(label="Add") #, command=NewFile)
        workoutmenu.add_command(label="Remove") #, command=OpenFile)

        # helpmenu = tk.Tk.Menu(menu)
        # menu.add_cascade(label="Help", menu=helpmenu)
        # helpmenu.add_command(label="About...", command=About)
        
        tabControl = ttk.Notebook(self) 
        tab0 = ttk.Frame(tabControl) 
        tab1 = ttk.Frame(tabControl) 
        tab2 = ttk.Frame(tabControl) 
        tab3 = ttk.Frame(tabControl) 
        tab4 = ttk.Frame(tabControl) 
          
        tabControl.add(tab0, text ='all') 
        tabControl.add(tab1, text ='running') 
        tabControl.add(tab2, text ='walking') 
        tabControl.add(tab3, text ='cycling') 
        tabControl.add(tab4, text ='swimming') 
        
        tabControl.pack(expand = 1, fill ="both")

        # filename_wrk='./activities/workouts2020-05--fit.csv'
        # filename_wrk='./t.csv'
        dfs0 = pd.read_csv(filename_wrk)
        dfs1 = dfs0.loc[dfs0['sport'] == 'running']
        dfs2 = dfs0.loc[dfs0['sport'] == 'walking']
        dfs3 = dfs0.loc[dfs0['sport'] == 'cycling']
        dfs4 = dfs0.loc[dfs0['sport'] == 'swimming']
        
        self.col_filename = dfs0.columns.get_loc('filename')
        
        #pt0 = Table(tab0, dataframe=dfs0, showtoolbar=False, showstatusbar=False)
        self.pt = table=Table(tab0, dataframe=dfs0, showtoolbar=False, showstatusbar=False)
        table.bind("<Double-Button-1>",self._handle_double_left_click)
        pt1 = Table(tab1, dataframe=dfs1, showtoolbar=False, showstatusbar=False)
        pt2 = Table(tab2, dataframe=dfs2, showtoolbar=False, showstatusbar=False)
        pt3 = Table(tab3, dataframe=dfs3, showtoolbar=False, showstatusbar=False)
        pt4 = Table(tab4, dataframe=dfs4, showtoolbar=False, showstatusbar=False)
        
        #self.pt = table = Table(tab1, dataframe=dfs1, showtoolbar=False, showstatusbar=False)
        #self.pt = table = Table(tab0, dataframe=dfs0, showtoolbar=False, showstatusbar=False)
        
        self.pt.show()
        pt1.show()
        pt2.show()
        pt3.show()
        pt4.show()
        
        self._childWindowCreate()
        self.ChildWindow.withdraw()

    def _handle_double_left_click(self, event): #,frame): #,pt):  #, childWindow):   
        
        # rowclicked = self.pt.get_row_clicked(event)
        # # rowclicked = self.pt.reset_index(drop=True).get_row_clicked(event)
        # id=self.pt.model.df.reset_index(drop=True)[rowclicked]
        # # filename=self.pt.model.df['filename'][id]
        # # filename=self.pt.model.df['filename'][rowclicked]
        # filename=self.dfs['filename'][id]
        
        row = self.pt.get_row_clicked(event)
        # col = self.pt.get_col_clicked(event)
        #crow = self.pt.getSelectedRow()
        col = self.col_filename
        # print(row,col)
        filename = TableModel(self.pt.model.df).getValueAt(row, col)
        # print(filename)
        if (filename[-4:] == '.fit') or (filename[-4:] == '.tkl'):
            self._childWindow(filename)

    def _childWindow(self, filename):
        if not self.ChildWindow.winfo_exists():
           self._childWindowCreate()
        else:
           self.ChildWindow.deiconify()
       
        if filename[-4:] == '.fit':
            df=fitdf.read_file(filename)
            label = df['timestamp'][0].strftime('%Y-%m-%d')
            x = df['distance']/1000
            ynames = ['pace', 'heart_rate', 'HRE']
        elif filename[-4:] == '.tkl':
            df=tkldf.read_file(filename) 
            label = df['date'][0].strftime('%Y-%m-%d')
            x = df['dist']/1000
            ynames = ['pace', 'HR', 'HRE']

          # k=0
        for k in range(len(ynames)):
        # for ax in self.fig.get_axes():
            ax=self.fig.get_axes()[k]
            yname = ynames[k]
            y = df[yname]
            ax.plot(x,y, label=label)
            ax.grid(True, linestyle='--')
            ax.set_ylabel(yname)
            ylimmean=df[yname].mean()
            ax.set_ylim([ylimmean*0.8,ylimmean*1.2])
               # k=+1
        ax.set_xlabel('distance (km)')
        ax.legend()
        self.fig.tight_layout() 
           
        self.canvas.draw()

           
    def _childWindowCreate(self):
        
        self.ChildWindow = tk.Toplevel(master=self, width=100, height=100)
        self.ChildWindow.title('Child window')
        self.ChildWindow.geometry("600x510+510+510")

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.fig.add_subplot(311)
        self.fig.add_subplot(312)
        self.fig.add_subplot(313)
        # A tk.DrawingArea.
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.ChildWindow)  
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        toolbar = NavigationToolbar2Tk(self.canvas, self.ChildWindow)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
    def menuquit(self):
        self.quit()     # stops mainloop
        self.destroy()

    def menuopen(self):
        # opens in the new windows as new application
        filename=easygui.fileopenbox(default="./activities/*.csv")
        App(filename).mainloop()
        # # opens in the same windows by updating the table
        # filename=easygui.fileopenbox(default="./activities/*.csv")
        
    def show_track(self):
        # opens in browser tab with track on the map
        row = self.pt.getSelectedRow()
        col = self.col_filename
        #print(row,col)
        filename = TableModel(self.pt.model.df).getValueAt(row, col)
        #print(filename)
       # track on the map
        fit_tkl=(filename[-4:] == '.fit') or (filename[-4:] == '.tkl')
        if fit_tkl:

            if filename[-4:] == '.fit':
                df=fitdf.read_file(filename) 
                dfpos=df[['position_lat', 'position_long']]. \
                            dropna(subset = ['position_lat', 'position_long']). \
                            rename(columns={'position_lat': 0, 'position_long': 1})
            elif filename[-4:] == '.tkl':
                df=tkldf.read_file(filename) 
                dfpos=pd.DataFrame.from_dict(zip(df['lat'], df['lon'])).dropna()

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
    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", help="workouts csv file")
    args = parser.parse_args()
    filename=args.filename
    if not filename:
        filename=easygui.fileopenbox(default="./activities/*.csv")
        # filename='./workouts2020-08-fit.csv'

    App(filename).mainloop()