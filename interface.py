import struct
import sys
import queue
import threading
import csv
from memory import MemoryManager

pages_in_system = 1000
pageSize = 691200  # Taman~o era de 691200B, Pagina de 192000 caracteres 
lock = threading.Lock()

class Interface:
	#La cola se recibe como parametro ya que fue creada por el servidor para 
	#compartirla con los recolectores.
	#Cada linea de la matriz(tabla) de la interfaz es asi:
	#[Thread_id, offset, pages_owned]

	def initializer(self, interface_queue, collectors_info, memoryManager):
		id_table=[]
		for entry in collectors_info:  
			pages_owned = []#[counter]
			row = [entry[4] ,0,  pages_owned]
			id_table.append(row)
		self.run(interface_queue, id_table, memoryManager)
	
	def run(self, interface_queue, id_table, memoryManager):
		thread = threading.Thread(target=self.plotRequested, args=(id_table, memoryManager))
		thread.start()
		thread = threading.Thread(target=self.dataEntry, args=(interface_queue,id_table, memoryManager) )
		thread.start()
		sensorRequestedData = -1   # Hubo / Cual sensor solicito datos

	def plotRequested(self, id_table, memoryManager): # Solicitud de graficar
		sensorRequestedPlot = -1
		while True:
			# Input era para probar
			sensorRequestedPlot = int(input()) # Funcion de Graficador solitando hacer plot,
			if sensorRequestedPlot > -1:
				data = []  # Es el que usa graficador
				#id_table[sensorRequestedPlot][2] = [1,4,5]
				for x in id_table[sensorRequestedPlot][2]:	
					lock.acquire()
					data.extend( memoryManager.sendPageToInterface(x) )
					lock.release()	
					# Pedir paginas uno a uno	

	def dataEntry(self, interface_queue, id_table, memoryManager):  # Ingreso de datos que se van paginar
			while True:
				if not interface_queue.empty():
					data_card = interface_queue.get()
					spaceUsed = id_table[data_card[1]][1]
					sensorPages = id_table[data_card[1]][2]
					if sensorPages:
						currentPage = sensorPages[len(sensorPages)-1]
					numberReceived = -1
					if pageSize > spaceUsed and spaceUsed > 0: # Hay espacio
						lock.acquire()
						memoryManager.writePage(currentPage,  data_card[0][0], data_card[0][1], spaceUsed)
						lock.release()
						id_table[data_card[1]][1] += sys.getsizeof(data_card[0])
					else: 					# No hay espacio
						# Pide nueva pagina
						lock.acquire()
						numberReceived = memoryManager.createNewPage()
						print(numberReceived)
						lock.release()
						if numberReceived != -1:
							lock.acquire()
							sensorPages.append(numberReceived)
							memoryManager.writePage(numberReceived, data_card[0][0], data_card[0][1], spaceUsed)
							lock.release()
							id_table[data_card[1]][1] = sys.getsizeof(data_card[0])
							#print("Size of Date = ", type(data_card[0][0]))
							#print("Size of Value = ", type(data_card[0][1]))
						else:
							print("Not enough space.")

	
