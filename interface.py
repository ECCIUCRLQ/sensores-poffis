import struct
import sys
import queue
import threading
import csv

pages_in_system = 1000
pages_owned = []

class Interface:
	#La cola se recibe como parametro ya que fue creada por el servidor para 
	#compartirla con los recolectores.
	#Cada linea de la matriz(tabla) de la interfaz es asi:
	#[Thread_id, offset, pages_owned]
	def initializer(interface_queue, collectors_info):
		id_table=[]
		for entry in collector_info:
			id_table.append(entry[4] ,0,  pages_owned)
		thread=threading.Thread(target=self.run, args =(interface_queue, id_table) )
		thread.start

	
	def run(interface_queue, id_table):
		while True:
			data_card=interface_queue.get()
			#Buscar en la tabla a quien pertenece
			#Comprobar que la pagina tiene espacio
			#Pedir más espacio y guardar o solo guardar 
		
