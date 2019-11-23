import random 
import struct
import sys
import queue
import threading
import time
import csv
from interface import Interface
from collectors import Collectors
from plotter import Plotter
from local_memory import MemoryManager


#tamaño de cola de mensajes sin imprimir
QUEUE_SIZE = 10000
GENERATION_TIME=1

def main():
	
	### Leer cuantos sensores hay conectados para poder realizar el handshake(malloc mágico)
	### Crear barrera con contador = cuantos sensores hay
	### Crear cola para cada thread
	### Crear semaforo para cada cola de rocolectores
	### Crear threads recolectores (se envía de parámetro su cola y su identificador respectivo)
	#abre el archivo csv en modo lectura
	interface_queue = queue.Queue(QUEUE_SIZE)
	memoryManager = MemoryManager()
	plotter = Plotter()
	interface = Interface()
	#plotter.initializer(interface)
	interface.initializer(interface_queue, collectors_info, memoryManager, plotter)

	
	while True:
		#Primer sensor
		#Paquete compuesto de la fecha y lectura
		package = [int(time.time()),random.randint(100,500)]
		interface_queue.put(package, 0)
		#Segundo sensor 
		package = [int(time.time()),random.randint(100,500)]
		interface_queue.put(package, 1)
		
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
