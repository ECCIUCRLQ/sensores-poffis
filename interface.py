import struct
import sys
import queue
import threading
import csv

pages_in_system = 1000
pages_owned = [] # Creo que se tiene que hacer diferente el append para que exista division de cuales paginas tiene cada sensor
sensorRequestedData = -1   # Hubo / Cual sensor solicito datos
pageSize = 691200  # Taman~o era de 691200B, Pagina de 192000 caracteres 

class Interface:
	#La cola se recibe como parametro ya que fue creada por el servidor para 
	#compartirla con los recolectores.
	#Cada linea de la matriz(tabla) de la interfaz es asi:
	#[Thread_id, offset, pages_owned]
	def initializer(self):#(interface_queue, collectors_info):
		id_table=[]
		for entry in collector_info:  
			id_table.append(entry[4] ,0,  pages_owned)
		thread=threading.Thread(target=self.run, args =(interface_queue, id_table) )
		thread.start
	
	def run(self, interface_queue, id_table):
		while True:
			if sensorRequestedData > -1: # Solicitud
				# Solicitar paginas del sensor que pidio data, una por una.
			elif not interface_queue.Empty(): # Ingreso
				data_card = interface_queue.get()
				spaceUsed = id_table[data_card[1]][1]
				sensorPages = id_table[data_card[1]][2]
				if pageSize > spaceUsed: # Hay espacio
					# Enviar direccion logica y offset.
				else: 					# No hay espacio
					# Pide nueva pagina
				numberReceived = -1
				currentPage = sensorPages[len(sensorPages)-1]
				while numberReceived == -1:
					if numberReceived == currentPage:
						id_table[data_card[1]][1] += sys.getsizeof(data_card[0])
					elif numberReceived != -1:
						sensorPages.append(numberReceived)

			#Buscar en la tabla a quien pertenece
			#Comprobar que la pagina tiene espacio
			#Pedir más espacio y guardar o solo guardar 
