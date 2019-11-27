import distributed_interface_protocol from DistributedInterfaceProtocol
import struct
import threading

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

class DistributedInterface
{
	def __init__(self):
		self.pageTable = [[None]*MAX_PAGE_COUNT]*INFO_PER_PAGE
		self.nodeTable = [[None]*MAX_NODE_COUNT]*INFO_PER_NODE
		
		## La primera columna indica el número de página (coincide con número de fila) y la segunda columna el id del nodo 
		## donde se encuentra guardada, con -1 se indica que la página aún no ha sido almacenada en ningún nodo (está en memoria local).
		for( row in range(0, MAX_PAGE_COUNT) ):
			for(col in range(0, INFO_PER_PAGE) ):
				if( col == PAGE_ID )
					self.pageTable[row][col] = row
				else:
					self.pageTable[row][col] = -1 
		
		## La primera columna indica el id del nodo (coincide con número de fila), la segunda indica su dirección IP y la tercera el espacio
		## disponible. Columnas 2 y 3 se inicializan en -1 para indicar que ese nodo aún no se ha registrado.
		for( row in range(0, MAX_NODE_COUNT) ):
			for(col in range(0, INFO_PER_NODE) ):
				if( col == NODE_ID_T )
					self.pageTable[row][col] = row
				else:
					self.pageTable[row][col] = -1 
	
		self.messenger =  DistributedInterfaceProtocol()
		self.messenger.run() 
		self.run() 
	
	def run(self):
		## Hilo que atiende solicitudes de IP por parte del protocolo, para guardar o solicitar páginas en un nodo.
		ipAssigner = threading.Thread(target = self.listenIpRequests)
		ipAssigner.start()
		## Hilo que atiende el registro de los nuevos nodos.
		newNodesReceptionist = threading.Thread(target = self.registerNewNode)
		newNodesReceptionist.start()
		
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
				nodeId = self.messenger. self.pageTable[self.messenger.pageId][NODE_ID]
				if( nodeId > -1 ):
					self.messenger.ipCurrentNode = self.nodeTable[nodeId][NODE_IP]
				else: ## Con -1 se le indica al protocolo que la página solicitada no está en ningún nodo.
					self.messenger.ipCurrentNode = nodeId
				
			self.messenger.iAlreadyKnowIp.release()
	
	def registerNewNode(self):
		##while True:
		
		
	def updatePageTable(self, pageId, nodeId):
		self.pageTable[pageId][NODE_ID] = nodeId
				
	def updateNodeTable(self, nodeId, nodeIp, availableSpace):
		self.nodeTable[nodeId][AVAILABLE_SPACE] = availableSpace
		self.nodeTable[nodeId][NODE_IP] = nodeIp
	
	# First fit.
	def selectNode(self, pageSize, pageId):
		assignedNode = -1
		for(row in self.nodeTable):
			if(row[AVAILABLE_SPACE] >= pageSize):
				assignedNode = row[NODE_ID_T]  
				updatePageTable(pageId, row[NODE_ID_T])
				break
				
		return assignedNode 
}
