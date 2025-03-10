"""
Created on Sat Mar 12 07:17:30 2022
@author: Pankaja Suganda
"""

# imported libraries (all required libraries included in requirement.txt file)
from tkinter import *
from tkinter import ttk
from tkinter import font
from PIL import Image, ImageTk

# importint plotting libraries
from matplotlib.backends.backend_tkagg import *
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor, MultiCursor
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")

# importing suppotive libraries
# from cursor import Cursor
from defines import *
from serial.tools import list_ports
import numpy as np
import pandas as pd
import serial
import logging
import time

class Application(Tk):
    """The main GUI class of the project

    Args:
        Tk (Tkinter Object): Tkinter object to develop GUI
    """

    def __init__(self):
        Tk.__init__(self)
        self.show = []

        self.spec_freq = []
        self.spec_pow  = []
        self.minsize(800,480)
        self.maxsize(800,480)
        self.Selected = False

        self.com_port = None
        self.create_widget()
        self.values_updater(10)

    """drawing all widget on the  page"""
    def create_widget(self):

        # Create a Graph
        self.fig    = Figure(figsize=(5,5), dpi=100, facecolor=GRAPH_COLOR)
        self.graph  = self.fig.add_subplot(111)
        self.graph.set_facecolor(GRAPH_COLOR)
        self.graph.xaxis.label.set_color(GRAPH_AXIS_COLOR)
        self.graph.yaxis.label.set_color(GRAPH_AXIS_COLOR)
        self.graph.tick_params(axis='x', colors=GRAPH_AXIS_COLOR)
        self.graph.tick_params(axis='y', colors=GRAPH_AXIS_COLOR)
        self.graph.set_xlabel("Frequency (Hz)")
        self.graph.set_ylabel("Power (dBm)")
        self.graph.grid()
        self.canvas = FigureCanvasTkAgg(self.fig, self)

        self.canvas.draw()
        self.canvas.get_tk_widget().place(x=0, y=30, height=385, width=725)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.config(background=BACKGROUND_COLOR)
        self.toolbar.update()

        slider_update = Scale(self, from_=1, to=50, orient=HORIZONTAL, bg=BACKGROUND_COLOR, fg=TEXT_COLOR, label="Frequency [Hz]")
        slider_update.place(x=665, y=150,  width=125)

        # adding the 'logo.jpg' image 
        r_image= Image.open('./images/logo.png').resize((150,40), Image.ANTIALIAS)
        self.logo = ImageTk.PhotoImage(r_image)
        
        self.logo_start = Label(self, width=150, height=50, bg=BACKGROUND_COLOR, fg='dark gray')
        self.logo_start.image = self.logo  
        self.logo_start.configure(image=self.logo)
        self.logo_start.place(x=5,y=5)

        # port selector combobox 
        self.port_selector = ttk.Combobox(self, textvariable="Select Port", width=15, values=list_ports.comports())
        self.port_selector.place(x=665, y=10)

        # port select
        self.btn_select = Button(self, text="Select", height=1, width=15, font =LABEL_FONT, command=self.Comport_select_event )
        self.btn_select.place(x=665, y=40)

        # port deselect
        self.btn_select = Button(self, text="Remove", height=1, width=15, font =LABEL_FONT, command=self.deAttachPort )
        self.btn_select.place(x=665, y=75)

        # creating paramters labels for top bar
        self.lblRefLevel = Label(self, text=REF_LABEL.format(ref = 0.00),  anchor="w", bg=BACKGROUND_COLOR, font =LABEL_FONT, fg =TEXT_COLOR, width = 17)
        self.lblRefLevel.place(x=170, y=10)

        self.lblAtt = Label(self, text=ATT_LABEL.format(att = 0.00),   anchor="w", bg=BACKGROUND_COLOR, font =LABEL_FONT, fg =TEXT_COLOR, width = 17)
        self.lblAtt.place(x=170, y=30)

        self.lblSWT = Label(self, text=SWT_LABEL.format(swt = 0.00),  anchor="w", bg=BACKGROUND_COLOR, font =LABEL_FONT, fg =TEXT_COLOR, width = 14)
        self.lblSWT.place(x=300, y=30)

        self.lblRVB = Label(self, text=RVB_LABEL.format(rvb = 0.00),  anchor="w", bg=BACKGROUND_COLOR, font =LABEL_FONT, fg =TEXT_COLOR, width = 17)
        self.lblRVB.place(x=400, y=10)

        self.lblVBW = Label(self, text=VBW_LABEL.format(vbw = 0.00),   anchor="w", bg=BACKGROUND_COLOR, font =LABEL_FONT, fg =TEXT_COLOR, width = 17)
        self.lblVBW.place(x=400, y=30)

        self.lblMode = Label(self, text=MODE_LABEL.format(mode = "Auto Mode"),   anchor="w", bg=BACKGROUND_COLOR, font =LABEL_FONT, fg =TEXT_COLOR, width = 17)
        self.lblMode.place(x=530, y=30)

        # creating paramters labels for bottom bar
        self.lblCenter_Freq = Label(self, text=CENTER_FREQ_LABEL.format(center_freq = 0.00),   anchor="w", font =LABEL_FONT, fg =TEXT_COLOR, bg=BACKGROUND_COLOR, width = 17)
        self.lblCenter_Freq.place(x=250, y=450)

        self.lblFreqDiv= Label(self, text=FREQUENCY_DIV.format(FreqDiv = 0.00),   anchor="w", font =LABEL_FONT, fg =TEXT_COLOR, bg=BACKGROUND_COLOR, width = 17)
        self.lblFreqDiv.place(x=370, y=450)

        self.lblSpan = Label(self, text=SPAN_LABEL.format(span = 0.00),   anchor="w", font =LABEL_FONT, fg =TEXT_COLOR, bg=BACKGROUND_COLOR, width = 17)
        self.lblSpan.place(x=490, y=450)

    def Comport_select_event(self):

        port = self.port_selector.get().replace(' ','').split('-')[0]
        self.com_port = serial.Serial(port=port, baudrate=BANDRATE_TIME, timeout=0) 
        self.Selected = True
        print(self.com_port)

    def deAttachPort(self):
        self.com_port.close()
        self.Selected = False

    def serialDataValidating(self, data):
        count = 0
        if data[0] == START_FLAG:
            while True:
                ch = data[count]
                count+=1
                if ch == END_FLAG:
                    return True
                if ch == '/n':
                    return False
        else:
            return False

    def readdata(self):
        x, y = [], []

        if not self.com_port == None and self.com_port.isOpen():
            try:
                data = self.com_port.readline().decode("utf-8").rstrip()
                if not (len(data) == 0):
                    data = data.split(',')

                    if(self.serialDataValidating(data)):
                        length = data[1]
                        for x_value in data[2:int(length) + 2]:
                            x.append(float(x_value))

                        for y_value in data[int(length) + 2: len(data)-2]:
                            y.append(float(y_value))

                        print(len(x), len(y))
                        if len(x) == len(y):
                            self.spec_freq = x
                            self.spec_pow = y
                        else: 
                            return None
                    else:
                        None
                return x, y
            except Exception as e:
                print(e)


    def values_updater(self, time):
        
        self.port_selector['values'] = list_ports.comports()
        self.readdata()
        if self.Selected:
            self.graph.clear()
            self.graph.set_xlabel("Frequency (Hz)")
            self.graph.set_ylabel("Power (dBm)")
            self.graph.grid()
            self.graph.plot(self.spec_freq,self.spec_pow,c=PLOTTING_COLOR)
 

""""main functon"""
if __name__ == "__main__":
    window = Application()
    window.geometry("800x480")                      # geometry settings for 7 inchs display
    #window.attributes('-toolwindow', True)
    window.configure(bg = BACKGROUND_COLOR)         # assigning background color
    update = animation.FuncAnimation(window.fig, \
         window.values_updater, interval=INTERVAL)  # value updating
    #window.wm_attributes('-fullscreen', 'True')     # this is for enable the full screen view
    window.wm_title(APPLICATION_TITLE)              # this is for enable the full screen view
    window.mainloop()