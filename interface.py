import struct
import sys
import queue
import threading
import csv

pages_in_system = 1000
pageSize = 691200  # Taman~o era de 691200B, Pagina de 192000 caracteres 
lock = threading.Lock()

class Interface:
	#La cola se recibe como parametro ya que fue creada por el servidor para 
	#compartirla con los recolectores.
	#Cada linea de la matriz(tabla) de la interfaz es asi:
	#[Thread_id, offset, pages_owned]
	def initializer(self, interface_queue, collectors_info):
		id_table=[]
		counter = 0
		for entry in collectors_info:  
			pages_owned = [counter]
			counter += 1
			row = [entry[4] ,0,  pages_owned]
			id_table.append(row)
		thread=threading.Thread(target=self.run, args =(interface_queue, id_table) )
		thread.start()
	
	def run(self, interface_queue, id_table):
		thread = threading.Thread(target=self.plotRequested, args=(id_table, ))
		thread.start()
		thread = threading.Thread(target=self.dataEntry, args=(interface_queue,id_table) )
		thread.start()
		sensorRequestedData = -1   # Hubo / Cual sensor solicito datos

	def plotRequested(self, id_table):
		sensorRequestedPlot = -1
		data = []
		while True:
			sensorRequestedPlot = int(input()) # Funcion de Graficador solitando hacer plot
			if sensorRequestedPlot > -1:
				lock.acquire()
				data = []
				#id_table[sensorRequestedPlot][2] = [1,4,5]
				for x in id_table[sensorRequestedPlot][2]:	
					#data.extend( solicitudPagina(x) )
					# Pedir paginas uno a uno	
				lock.release()	

	def dataEntry(self, interface_queue, id_table):
			while True:
				if not interface_queue.empty():
					data_card = interface_queue.get()
					spaceUsed = id_table[data_card[1]][1]
					sensorPages = id_table[data_card[1]][2]
					currentPage = sensorPages[len(sensorPages)-1]
					numberReceived = -1
					if pageSize > spaceUsed: # Hay espacio
						lock.acquire()
						# currentPage,spaceUsed
						# Enviar direccion logica (Pagina actual) y offset (spaceUsed).
						# numberReceived = funcion que retorna numero de pagina
						id_table[data_card[1]][1] += sys.getsizeof(data_card[0])
						lock.release()
					else: 					# No hay espacio
						lock.acquire()
						# Pide nueva pagina
						# numberReceived = funcion que retorna numero de pagina 
						sensorPages.append(numberReceived)
						id_table[data_card[1]][1] = sys.getsizeof(data_card[0])
						lock.release()

	
