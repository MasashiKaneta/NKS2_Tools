#!/usr/bin/env python3


import os
import glob
import time
import datetime
import threading
import tkinter as tk
import re
import simpleaudio as sa


default_threshold_temp = 40

# Setting to use relay 
# The orger in the following lines are for ch 1, 2, 3, 4
os.system('gpio -g mode 19 out')
os.system('gpio -g mode 26 out')
os.system('gpio -g mode 20 out')
os.system('gpio -g mode 21 out')

# Load 1-wire and thermo-sensor module
os.system('/sbin/modprobe w1-gpio')
os.system('/sbin/modprobe w1-therm')
 
# Voice for the events
wave_obj  = sa.WaveObject.from_wave_file("./set_threshold.wav")
wave_obj2 = sa.WaveObject.from_wave_file("./alert.wav")
wave_obj3 = sa.WaveObject.from_wave_file("./Bias_voltage_On.wav")


# DS18B20 serial numbers. The order of list is TagB number
tagb_therm = [
               '28-00000ab154b8',
               '28-00000ab154f9',
               '28-00000ab16469',
               '28-00000ab1cc93',
               '28-00000ab1d2e4',
               '28-00000ab1d92a',
               '28-00000ab20f4b',
               '28-00000ab23bb4',
               '28-00000ab24b17',
               '28-00000ab27ad6',
               '28-00000ab6f020',
               '28-00000ab2ab34',
               '28-00000ab6fcd9',
               '28-00000ab6fd88',
               '28-00000ab71cbb',
               '28-00000ab72dc3',
               '28-00000ab73c1f',
               '28-00000ab741e5',
               '28-00000ab74299',
               '28-00000ab74319',
               '28-00000ab7520f',
               '28-00000ab7d083',
               '28-00000ab7abec',
               '28-00000ab7e331',
               '28-00000ab7a59f',
               '28-00000ab7e7c8',
               '28-00000ab81c4a',
               '28-00000ab838d9',
               '28-00000ab87014',
               '28-00000ab87cb5'
             ]

nd             = len(tagb_therm)
base_dir       = '/sys/bus/w1/devices/'
device_folders = []

for tg in tagb_therm:
    device_folders.append( base_dir + tg )

#----------------------------------------------

device_files = []
for df in device_folders:
    device_files.append( df + '/w1_slave'  )


#----------------------------------------------

def read_rom(i):
    name_file=device_folders[i]+'/name'
    f = open(name_file,'r')
    return f.readline()
 
#----------------------------------------------

def read_temp_raw(i):
    f = open(device_files[i], 'r')
    lines = f.readlines()
    nl = len(lines)
    while  nl < 1:
        d_t =  datetime.datetime.now()
        datetime_text =  d_t.strftime("%Y/%m/%d %H:%M:%S")

        print ( 'No data read from ' + device_files[i] + ' ' + datetime_text )
        lines = f.readlines()
        nl = len(lines)
#       time.sleep(0.2)

    f.close()
    return lines
 
#----------------------------------------------

def read_temp(i):
    lines = read_temp_raw(i)
    # Analyze if the last 3 characters are 'YES'.
    while lines[0].strip()[-3:] != 'YES':
#        time.sleep(0.2)
        lines = read_temp_raw(i)

    # Find the index of 'crc=' in a string.
    equals_pos = lines[0].find('crc=')
    if equals_pos != -1:
        # Read crc .
        crc_string = lines[0][equals_pos+4:equals_pos+6]
    # Find the index of 't=' in a string.
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        # Read the temperature .
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c

#----------------------------------------------  make window

class Monitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title( "Temperature monitor" )
        self.root.geometry("500x600")
        self.tval = default_threshold_temp

        # threshold of temperature for interlock
        self.threshold = tk.Label(self.root,text="Threshold: "+str(self.tval)+"C")
        self.threshold.place(x=130,y=500)

        self.entry = tk.Entry(self.root,width=5)
        self.entry.place(x=270,y=500)

        self.button = tk.Button(self.root,text='set', command=self.click)
        self.button.place(x=370,y=500)

        # interlock reset button
        self.ilstatus = tk.Label(self.root,text="Low Voltage: on")
        self.ilstatus.place(x=130,y=550)

        self.button2 = tk.Button(self.root,text='Reset interlock', command=self.resetil)
        self.button2.place(x=320,y=550)

        # quit button in menu bar
        self.menu1 = tk.Menu( self.root )
        self.root.config( menu=self.menu1 )
        self.menu_file = tk.Menu( self.root )
        self.menu1.add_cascade( labe='File', menu=self.menu_file )
        self.menu_file.add_command( label='Quit', command=self.quit )

        # relay control on
        os.system('gpio -g write 19 0')
        os.system('gpio -g write 26 0')
        os.system('gpio -g write 20 0')
        os.system('gpio -g write 21 0')

        self.frame = list(range(nd))
        self.la0   = list(range(nd))
        self.la1   = list(range(nd))
        for num in range(nd):
            self.frame[num] = tk.Frame(self.root,padx=1,pady=1,relief="flat",bd=5)
            self.frame[num].grid(column=num//6, row=num%6)

            self.la0[num] = tk.Label(self.frame[num])
            self.la0[num]["font"] = ("Helvetica", 20)
            self.la0[num]["bg"] = "green"
            self.la0[num]["fg"] = "white"
            self.la0[num]["text"] = "------"
            self.la0[num].grid(column=0, row=0)

            self.la1[num] = tk.Label(self.frame[num])
            self.la1[num]["font"]   = ("Helvetica", 10)
            self.la1[num]["text"]   = ("TagB "+str(num+1))
            self.la1[num]["bg"]     = "green"
            self.la1[num]["fg"]     = "white"
            self.la1[num]["anchor"] = tk.W
            self.la1[num].grid(column=0, row=1)

    def click(self):
        self.tval = re.sub( r"\D", "", self.entry.get() )
        if self.tval == '':
            self.tval = default_threshold_temp

        self.entry.delete(0,tk.END)
        self.threshold["text"] = 'Threshold: ' + str(self.tval) + 'C'

        play_obj = wave_obj.play()

    def resetil(self):
        self.ilstatus["text"] = 'Low Voltage: On'
        self.ilstatus["fg"] = "black"

        play_obj3 = wave_obj3.play()

        os.system('gpio -g write 19 0')
        os.system('gpio -g write 26 0')
        os.system('gpio -g write 20 0')
        os.system('gpio -g write 21 0')

        self.alert_flag = False

    def changeLabelText(self):
        self.alert_flag = False
        while True:
            for num in range(nd):
                temp = read_temp(num)
                self.la0[num]["text"] = '{:.1f}'.format(temp) + ' C'
                self.la0[num]["fg"]   = "black"

                if  float(temp) > float(self.tval):
                    self.alert_flag       = True

                    self.la0[num]["fg"]   = "red"

                    self.ilstatus["text"] = 'Interlock: On (LV: OFF)'
                    self.ilstatus["fg"]   = "red"

                    os.system('gpio -g write 19 1')
                    os.system('gpio -g write 26 1')
                    os.system('gpio -g write 20 1')
                    os.system('gpio -g write 21 1')
                else:
                    if num != 0:
                        pnum = num-1
                    else:
                        pnum = nd-1
                    self.la0[pnum]["fg"] = "white"

                if self.alert_flag == True:
                    play_obj2 = wave_obj2.play()

    def quit(self):
        self.root.destroy()


#--------------------------------------- threding

if __name__ == "__main__":
    monitor = Monitor()
    thread = threading.Thread(target=monitor.changeLabelText)
    thread.start()
    monitor.root.mainloop()

