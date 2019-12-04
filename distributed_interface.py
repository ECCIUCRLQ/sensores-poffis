
from distributed_interface_protocol import DistributedInterfaceProtocol
import struct
import threading
import time
from time import sleep

## Page table number of rows.
MAX_PAGE_COUNT = 256

## Page table number of columns.
INFO_PER_PAGE = 2

## Page table column identifiers.
PAGE_ID = 0 
NODE_ID =  1

## Node table number of rows.
MAX_NODE_COUNT = 256

## Node table number of columns.
INFO_PER_NODE = 3

## Node table column identifiers.
NODE_ID_T = 0
NODE_IP =  1
AVAILABLE_SPACE = 2

## Operation codes.
SAVE_PAGE = 0
REQUEST_PAGE = 1

class DistributedInterface:
	def __init__(self):
		self.lock = threading.Lock()
		self.pageTable = [None]*MAX_PAGE_COUNT	
		self.nodeTable = [None]*MAX_NODE_COUNT
		self.changesInPageTable = [False]*MAX_PAGE_COUNT
		self.changesInNodeTable = [False]*MAX_NODE_COUNT
		## La primera columna indica el número de página (coincide con número de fila) y la segunda columna el id del nodo 
		## donde se encuentra guardada, con -1 se indica que la página aún no ha sido almacenada en ningún nodo (está en memoria local).
		for row in range(0, MAX_PAGE_COUNT):
			self.pageTable[row] = [None]*INFO_PER_PAGE
			for col in range(0, INFO_PER_PAGE):
				if( col == PAGE_ID ):
					self.pageTable[row][col] = row
				else:
					self.pageTable[row][col] = -1 
		
		## La primera columna indica el id del nodo (coincide con número de fila), la segunda indica su dirección IP y la tercera el espacio
		## disponible. Columnas 2 y 3 se inicializan en -1 para indicar que ese nodo aún no se ha registrado.
		for row in range(0, MAX_NODE_COUNT) :
			self.nodeTable[row] = [None]* INFO_PER_NODE
			for col in range(0, INFO_PER_NODE) :
				if( col == NODE_ID_T ):
					self.nodeTable[row][col] = row
				else:
					self.nodeTable[row][col] = -1 
	
		self.messenger =  DistributedInterfaceProtocol()
		tablesReceived = self.messenger.run()
		if(self.messenger.iAmIDActive):
			self.run()
		else:
			if(tablesReceived != None):
				#Se actualizan tablas según tablesReceived
				self.updateTables(tablesReceived)
				print("Ya estoy al día con las tablas")
				#print("actualicé tablas")
				#print(self.nodeTable)
				#print(self.pageTable)
			while not self.messenger.iAmIDActive:
				timeout = time.time() + 2
				while(time.time() < timeout):
					if not self.messenger.keepAliveQueue.empty():
						tablesReceived = self.messenger.keepAliveQueue.get()
						if(not tablesReceived == None):
							#Actualizar tablas
							self.updateTables(tablesReceived)
							#print("actualicé tablas")
							
						timeout = time.time() + 2
				self.messenger.iAmIDActive,tablesReceived = self.messenger.champions(False)
			self.messenger.runActive()
			self.run()
	
	def run(self):
		## Hilo que atiende solicitudes de IP por parte del protocolo, para guardar o solicitar páginas en un nodo.
		ipAssigner = threading.Thread(target = self.listenIpRequests)
		ipAssigner.start()
		## Hilo que atiende el registro de los nuevos nodos.
		newNodesReceptionist = threading.Thread(target = self.registerNewNode)
		newNodesReceptionist.start()
		# Crear hilo que esté enviando los cambios a las tablas cada 2 segundos
		sendKeepAlivesThread = threading.Thread(target = self.sendKeepAlivesToIDs)
		sendKeepAlivesThread.start()

		
	def listenIpRequests(self):
		while True:
			self.messenger.idTellMeTheIp.acquire()
			
			## Si se requiere guardar una página se selecciona un nodo utilizando Fist Fit y se retorna su IP.
			if( self.messenger.currentOperation == SAVE_PAGE ):
				assignedNode = self.selectNode(self.messenger.pageSize, self.messenger.pageId)
				if( assignedNode > -1 ): 
					self.messenger.ipCurrentNode = self.nodeTable[assignedNode][NODE_IP]
				else: ## Con -1 se le indica al protocolo que no se encontró espacio disponible para guardar en ningún nodo.
					self.messenger.ipCurrentNode = assignedNode 					
			## Si se requiere solicitar una página se localiza el nodo donde se encuentraß y se retorna su IP.
			elif( self.messenger.currentOperation == REQUEST_PAGE ):
				nodeId =  self.pageTable[self.messenger.pageId][NODE_ID]
				if( nodeId > -1 ):
					self.messenger.ipCurrentNode = self.nodeTable[nodeId][NODE_IP]
				else: ## Con -1 se le indica al protocolo que la página solicitada no está en ningún nodo.
					self.messenger.ipCurrentNode = nodeId
				
			self.messenger.iAlreadyKnowIp.release()

			if(self.messenger.currentOperation == SAVE_PAGE):
				self.messenger.okeyAlreadyRead.acquire()
				self.updateNodeTable(assignedNode,self.nodeTable[assignedNode][1],self.messenger.sizeInNode)
	
	def registerNewNode(self):
		nodes = 0
		while True:
			if(not self.messenger.newNodes.empty()):
				
				nodeInfo = self.messenger.newNodes.get()
				size = nodeInfo[0]
				Ip = nodeInfo[1]
				self.updateNodeTable(nodes,Ip,size)
				nodes = nodes + 1
				print(Ip)
		
		
	def updatePageTable(self, pageId, nodeId):
		self.lock.acquire()
		self.pageTable[pageId][NODE_ID] = nodeId
		self.changesInPageTable[pageId] = True
		self.lock.release()
				
	def updateNodeTable(self, nodeId, nodeIp, availableSpace):
		self.lock.acquire()
		self.nodeTable[nodeId][AVAILABLE_SPACE] = availableSpace
		self.nodeTable[nodeId][NODE_IP] = nodeIp
		self.changesInNodeTable[nodeId] = True
		self.lock.release()

	def updateTables(self, tablesReceived):
		assert(not (tablesReceived == None))
		for x in range (0,len(tablesReceived[0])): #Lista con cambios a la page table
			self.updatePageTable(tablesReceived[0][x][0],tablesReceived[0][x][1])

		for x in range (0,len(tablesReceived[1])): #Lista con cambios en la node table
			self.updateNodeTable(tablesReceived[1][x][0],tablesReceived[1][x][1],tablesReceived[1][x][2])



	# First fit.
	def selectNode(self, pageSize, pageId):
		assignedNode = -1
		for row in self.nodeTable:
			if(row[AVAILABLE_SPACE] >= pageSize):
				assignedNode = row[NODE_ID_T]  
				self.updatePageTable(pageId, row[NODE_ID_T])
				break
				
		return assignedNode 

	def sendKeepAlivesToIDs(self):
		while(True):
			sleep(0.5)
			self.lock.acquire()
			self.messenger.sendKeepAlive(self.pageTable,self.changesInPageTable,self.nodeTable,self.changesInNodeTable)
			for x in range (0,MAX_PAGE_COUNT):
				self.changesInPageTable[x] = False

			for x in range (0,MAX_NODE_COUNT):
				self.changesInNodeTable[x] = False

			if(not (self.messenger.iWantToBeQueue.empty())):
				self.sendIAmActiveToIDs()

			self.lock.release()
	
	def sendIAmActiveToIDs(self):
		pageCount = 0
		nodeCount = 0
		pageList = []
		nodeList = []
		for x in range (0,MAX_PAGE_COUNT):
			if(self.pageTable[x][1] > -1):
				pageCount = pageCount + 1
				pageList.append((self.pageTable[x][0],self.pageTable[x][1]))

		for x in range (0,MAX_NODE_COUNT):
			if(self.nodeTable[x][2] > -1):
				nodeCount = nodeCount + 1
				nodeList.append((self.nodeTable[x][0],self.nodeTable[x][1],self.nodeTable[x][2]))

		self.messenger.sendIAmChampion(pageCount,nodeCount,pageList,nodeList)



kappa = DistributedInterface()

