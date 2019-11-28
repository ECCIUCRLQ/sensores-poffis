import struct
import sys
import queue
import threading
import csv
from local_memory import MemoryManager
from plotter import Plotter

PAGES_IN_SYSTEM = 4
#3600s * 24h * 2ints-of-data
#PAGE_SIZE = 172800
PAGE_SIZE = 10
#Flag values
NOT_FULL = 0
FULL = 1

class Interface:
	lock = None
	#La cola se recibe como parametro ya que fue creada por el servidor para
	#compartirla con los recolectores.
	#Cada linea de la matriz(tabla) de la interfaz es asi:
	#[Thread_id, offset, pages_owned]
	def initializer(self, interface_queue, memoryManager, plotter):
		id_table=[]
		self.lock = threading.Lock()
		for sensors in range(2):
			pages_owned = []#[counter]
			row = [sensors ,0,  pages_owned]
			id_table.append(row)

		self.run(interface_queue, id_table, memoryManager, plotter)

	def run(self, interface_queue, id_table, memoryManager, plotter):
		thread = threading.Thread(target=self.plotRequested, args=(id_table, memoryManager,plotter))
		thread.start()
		thread = threading.Thread(target=self.dataEntry, args=(interface_queue,id_table, memoryManager) )
		thread.start()

	def plotRequested(self, id_table, memoryManager, plotter):
		sensorRequestedPlot = -1
		counter = 0
		print("Primer Sensor: ")
		while True:
			print("Digite cuantos sensores desea graficar")
			numSensorsWanted = int(input())
			plotter.dataBuffer[:]=[]
			plotter.dataBuffer = [None] * numSensorsWanted
			for x in range(0,numSensorsWanted):
				print("Digite sensor numero", x, ": ")
				sensorRequestedPlot = int(input())
				if sensorRequestedPlot > -1:
					counter += 1
					plotter.dataBuffer[x] = []
					for v in id_table[sensorRequestedPlot][2]:
						self.lock.acquire()
						plotter.dataBuffer[x].extend( memoryManager.requestPage(v) )
						self.lock.release()

			if counter == numSensorsWanted:
				plotter.plot(numSensorsWanted)
				counter = 0

	def dataEntry(self, interface_queue, id_table, memoryManager):
			while True:
				if not interface_queue.empty():
					dataCard = interface_queue.get()
					spaceUsed = id_table[dataCard[2]][1]
					sensorPages = id_table[dataCard[2]][2]
					if sensorPages:
						currentPage = sensorPages[len(sensorPages)-1]
					numberReceived = -1
					if PAGE_SIZE > spaceUsed and spaceUsed > 0:
						self.lock.acquire()
						if (spaceUsed + 2) == PAGE_SIZE:
							memoryManager.writePage(currentPage,  dataCard[0], dataCard[1], spaceUsed, FULL)
						else:
							memoryManager.writePage(currentPage,  dataCard[0], dataCard[1], spaceUsed, NOT_FULL)
						id_table[dataCard[2]][1] += 2
						self.lock.release()
					else:
						self.lock.acquire()
						numberReceived = memoryManager.createNewPage()
						if numberReceived != -1:
							sensorPages.append(numberReceived)
							spaceUsed = 0
							memoryManager.writePage(numberReceived, dataCard[0], dataCard[1], spaceUsed, NOT_FULL)
							id_table[dataCard[2]][1] = 2
							self.lock.release()
						else:
							self.lock.release()
							print("Not enough space.")
