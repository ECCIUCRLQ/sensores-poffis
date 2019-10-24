import struct
import sys
import queue
import threading
#import numpy
#import tkinter
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import matplotlib.dates as mdates

class Plotter:
	def plot(self, data,n):
		fig, subplot = plt.subplots(n,sharex=True)
		fig.suptitle('Gráficado por POFFIS')
		for i in range(0,n):
			axisX = []
			axisY = []
			for x in range(0,len(data[i]),2):
				#if (x % 4 == 0):
				d = int(data[i][x])
				date = datetime.utcfromtimestamp(d-21600)
				axisX.append(date)
				axisY.append(data[i][x+1])
			subplot[i].plot(axisX,axisY)
			plt.xlabel("Fechas")
			plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M - %m/%d/%Y'))
			plt.gcf().autofmt_xdate()
			fig.set_size_inches(10, 7)
		fig.savefig('b.png', dpi=100)	
		print("Graficado!")
