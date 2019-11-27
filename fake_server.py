import random 
import struct
import sys
import queue
import threading
import time
import csv
from interface import Interface
from plotter import Plotter
from local_memory import MemoryManager


#tamaño de cola de mensajes sin imprimir
QUEUE_SIZE = 10000
GENERATION_TIME=1

def main():
	
	interface_queue = queue.Queue(QUEUE_SIZE)
	memoryManager = MemoryManager()
	plotter = Plotter()
	interface = Interface()
	interface.initializer(interface_queue, memoryManager, plotter)

	
	while True:
		#Package composed by date and data
		#First sensor
		package = [int(time.time()),random.randint(100,500),0]
		interface_queue.put(package)
		#Second sensor 
		package = [int(time.time()),random.randint(100,500),1]
		interface_queue.put(package)
		
		time.sleep(GENERATION_TIME)

main()

	

"""Protocolo del cliente al servidor	
Random ID	1 byte
Date	4 bytes
SensorID	4 bytes
Tipo de sensor	1 byte
Datos	
	
Protocolo servidor-cliente	
Random ID	1 byte
Sensor ID	4 bytes"""
