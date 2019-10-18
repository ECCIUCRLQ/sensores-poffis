import struct
import sys
import queue
import threading
import csv

pages_in_system = 1000

class Interface:
	def initializer(interface_queue, collectors_info):
		id_table=[]
		for entry in collector_info:
			id_table.append(entry[0], entry[1], 0,  queue.Queue(pages_in_system))
		thread=threading.Thread(target=self.run, args =(interface_queue, id_table) )
		thread.start

	
	def run(interface_queue, id_table):
		while True:
			data_card=interface_queue.get()
			#Buscar en la tabla a quien pertenece
			#Comprobar que la pagina tiene espacio
			#Pedir más espacio y guardar o solo guardar 
		
