import struct
import sys
import queue
import threading
import numpy
import matplotlib.pyplot as plt

class Plotter:
	
	def initializer(self, interface):
		thread = threading.Thread(target=self.run, args =(interface) )
		thread.start()
		
		
	def request_data(interface):
		#Este proceso usa al objeto interfaz para pedir datos
	
	
	def run(self, interface):
		#Este proceso llama a request data
		#Y grafica con matplotlib
