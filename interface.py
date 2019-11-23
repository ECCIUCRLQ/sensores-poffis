import struct
import sys
import queue
import threading
import csv
from memory import MemoryManager
from plotter import Plotter

pages_in_system = 1000
pageSize = 691200  # Taman~o era de 691200B, Pagina de 192000 caracteres 
lock = threading.Lock()

class Interface:
	#La cola se recibe como parametro ya que fue creada por el servidor para 
	#compartirla con los recolectores.
	#Cada linea de la matriz(tabla) de la interfaz es asi:
	#[Thread_id, offset, pages_owned]
	def initializer(self, interface_queue, collectors_info, memoryManager, plotter):
		id_table=[]
		for entry in collectors_info:  
			pages_owned = []#[counter]
			row = [entry[4] ,0,  pages_owned]
			id_table.append(row)
		self.run(interface_queue, id_table, memoryManager, plotter)
	
	def run(self, interface_queue, id_table, memoryManager, plotter):
		thread = threading.Thread(target=self.plotRequested, args=(id_table, memoryManager,plotter))
		thread.start()
		thread = threading.Thread(target=self.dataEntry, args=(interface_queue,id_table, memoryManager) )
		thread.start()
		#sensorRequestedData = -1   # Hubo / Cual sensor solicito datos

	def plotRequested(self, id_table, memoryManager, plotter): # Solicitud de graficar
		sensorRequestedPlot = -1
		counter = 0
		
		print("Primer Sensor: ")
		while True:
			print("Digite cuantos sensores desea graficar")
			numSensorsWanted = int(input())
			data = [None] * numSensorsWanted #inicialización del vector con nulos, estos van a ser las filas de la matriz
			for x in range(0,numSensorsWanted):
				print("Digite sensor numero", x, ": ")
				sensorRequestedPlot = int(input()) #plotter.getRequestedData() # Funcion de Graficador solitando hacer plot
				if sensorRequestedPlot > -1:
					counter += 1
					data[x] = [] #Aca se le asigna n vector a cada fila para construir las columnas de la matriz
					for v in id_table[sensorRequestedPlot][2]:	
						lock.acquire()
						data[x].extend( memoryManager.sendPageToInterface(v) ) #Append de un vector
						lock.release()	
						# Pedir paginas uno a uno	
			if counter == numSensorsWanted:
				plotter.plot(data,numSensorsWanted)
				counter = 0

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
						#print(numberReceived)
						lock.release()
						if numberReceived != -1:
							lock.acquire()
							sensorPages.append(numberReceived)
							#print(sensorPages)
							memoryManager.writePage(numberReceived, data_card[0][0], data_card[0][1], spaceUsed)
							lock.release()
							id_table[data_card[1]][1] = sys.getsizeof(data_card[0])
						else:
							print("Not enough space.")

	
