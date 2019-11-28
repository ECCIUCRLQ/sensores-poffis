import struct
import queue
import threading
import time
import socket
from time import sleep  

## Operation codes.
SAVE_PAGE = 0
REQUEST_PAGE = 1
OK = 2
SEND = 3
ERROR = 4
IAMHERE = 5

## Queue size.
QUEUE_SIZE = 10000

## Page size
PAGE_SIZE = 691200

## Data size.
DATA_SIZE = 4

## Number of integers peer page.
DATA_COUNT = PAGE_SIZE // DATA_SIZE


class DistributedInterfaceProtocol:
	receiveFromNodes = None
	## Request pages by local memory.
	requestedPages = None 
	## Pages to save for local memory.
	pagesToSave = None
	ok = None
	pages = None
	newNodes = None
	ipCurrentNode = None
	idTellMeTheIp =  None
	iAlreadyKnowIp = None 
	okeyAlreadyRead = None
	currentOperation = None
	pageSize =  None
	pageId = None
	socketML = None
	socketMD = None
	waitingForMD = None
	waitingToSendToML = None
	sizeInNode = 0
	
	def __init__(self):
		self.receiveFromNodes = queue.Queue(QUEUE_SIZE) 
		self.requestedPages = queue.Queue(QUEUE_SIZE) 
		self.pagesToSave = queue.Queue(QUEUE_SIZE) 
		self.ok = queue.Queue(QUEUE_SIZE) 
		self.pages = [None]*(DATA_COUNT) 
		self.newNodes = queue.Queue(QUEUE_SIZE)
		self.ipCurrentNode = ''
		self.idTellMeTheIp = threading.Semaphore(0)
		self.iAlreadyKnowIp = threading.Semaphore(0)
		self.okeyAlreadyRead = threading.Semaphore(0)
		self.currentOperation = -1
		self.pageId = -1
		self.pageSize = 0
		self.socketML = None
		self.socketMD = None
		self.waitingForMD = False
		self.waitingToSendToML = False
		self.sizeInNode = None
		
	def run(self):
		classifierML = threading.Thread(target = self.classifyPacketsFromML) 
		classifierMD = threading.Thread(target = self.classifyPacketsFromMD)
		classifierBroadcast = threading.Thread(target = self.classifyPacketsFromBroadcasts)
		requester = threading.Thread(target = self.requestPage)
		saver = threading.Thread(target = self.savePage)
		sender = threading.Thread(target=self.sendPage)
		classifierML.start()
		classifierMD.start()
		classifierBroadcast.start()
		requester.start()
		saver.start()
		sender.start()

		
	def savePage(self):	
		## Proteger con mutex.
		while True:
			if( not self.pagesToSave.empty() ):
				pageRequest =  self.pagesToSave.get()
				## Queremos guardar una página, ocupamos que ID nos diga la IP del nodo donde se guarda.
				self.currentOperation = SAVE_PAGE
				### Obtener número de página.
				self.pageId = pageRequest[1]
				### Obtener tamano de página.
				self.pageSize = pageRequest[2] 
				### Esperar que ID activa me diga la IP del nodo en el que hay que guardar.
				self.idTellMeTheIp.release()
				### ID activa avisa que ya nos dio la IP.
				self.iAlreadyKnowIp.acquire()
				## Si la ID distribuida retorna -1 en la IP es porque no había espacio para guardar la página (no debería suceder, pero por si acaso).
				if( self.ipCurrentNode > -1 ):
					packetStruct = struct.Struct('1s 1s I')
					for x in range (0,self.pageSize):
						packetStruct = packetStruct + ' I'
					packet = []
					packet.append( bytearray([pageRequest[0]]))
					packet.append( bytearray([pageRequest[1]]))
					packet.append( pageRequest[3])
					for x in range (0,self.pageSize):
						packet.append(pageRequest[x+3])
					pageToSend = packetStruct.pack(*(tuple(packet)))

					self.socketMD = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
					port = 6000
					connected = False
					while not connected:
						try:  
							self.socketMD.connect( ( self.ipCurrentNode, port ) )  
							connected = True  
							#print( "connection successful" )  
						except socket.error:
							print( "no Node" )  #No debería de pasar
							sleep( 2 )

					self.socketMD.send(pageToSend)
					self.waitingForMD = True
					timeout = time.time() + 10
					okFromDM = False
					packet = []
					while True:
						if(self.ok.empty()):
							if(time.time() > timeout):
								self.pagesToSave.put(pageRequest)
								self.waitingToSendToML = False
								break
						else:
							okMessage = self.ok.get()
							#self.ok.put(okMessage) #REVISAR
							
							
							if(okMessage[0] == ERROR):
								self.okeyAlreadyRead.release()
								print('Error: Could not save page.')
							else:
								okFromDM = True
							break
					if(okFromDM):
						packetStruct = struct.Struct('1s 1s')
						packet.append(bytearray(OK))
						packet.append(bytearray(okMessage[1]))
						self.sizeInNode = okMessage[2]
						sendInfo = packetStruct.pack( *( tuple(packet) ) )
						self.socketML.send(sendInfo)
						self.socketMD.close()
						self.waitingToSendToML = False
						self.okeyAlreadyRead.release()
				
												
	def requestPage(self):
		while True:
			##Proteger con mutex
			if( not self.requestedPages.empty() ):
				packet = []
				pageToRequest = self.requestedPages.get()
				self.currentOperation = REQUEST_PAGE
				self.idTellMeTheIp.release()
				self.iAlreadyKnowIp.acquire()
				## Si la ID distribuida retorna -1 en la IP es porque la página no está en ningún nodo (está en memoria local y fue error nuestro solicitarla).
				if( self.ipCurrentNode > - 1 ):
					packetStruct = struct.Struct('1s 1s')
					packet.append(bytearray(REQUEST_PAGE))
					packet.append(bytearray(pageToRequest))
					packetData = packetStruct.pack(*(tuple(packet)))
					self.socketMD = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
					port = 6000
					connected = False
					while not connected:
						try:  
							self.socketMD.connect( ( self.ipCurrentNode, port ) )  
							connected = True  
							#print( "connection successful" )  
						except socket.error:
							print( "no Node" )  
							sleep( 2 )
					self.socketMD.send(packetData)
					self.waitingForMD = True

					
		
	def sendPage(self):
		while True: 
			#Proteger con Mutex
			if(not self.receiveFromNodes.empty()):
				self.currentOperation = SEND
				packageReceived = self.receiveFromNodes.get()
				self.socketML.send(packageReceived)
				self.socketML.close()
				self.waitingToSendToML = False
				
		
		
		
				
	def classifyPacketsFromML(self): ## Desempaquetar solo para verificar códigos de operación, en las colas deben guardarse como vienen.
		while True:
			packetStruct = struct.Struct('1s')
			while True:
				if(not self.waitingToSendToML):
					s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
					host = '192.168.1.31' #socket.gethostname()  
					port = 6000
					s.bind( ( host, port ) )  
					s.listen( 1 )
					self.socketML,addr = s.accept()
					data = self.socketML.recv(700000)
					if(data):
						self.waitingToSendToML = True
						#print(data)
						unpackedData = list(packetStruct.unpack(data[:1]))
						operationCode =  struct.unpack('>H',b'\x00' + unpackedData[0] )[0]
						if(operationCode == REQUEST_PAGE):
							packetStruct = struct.Struct('1s 1s')
							unpackedData = list(packetStruct.unpack(data[:2]))
							operationCode = struct.unpack('>H',b'\x00' + unpackedData[0])[0]
							pageID = struct.unpack('>H',b'\x00' + unpackedData[1])[0]
							data = pageID
							self.requestedPages.put(data)
						elif(operationCode == SAVE_PAGE):
							packetFormat = '1s 1s I'
							packetStruct = struct.Struct(packetFormat)
							unpackedData = list(packetStruct.unpack(data[:8]))
							size = unpackedData[2]
							for x in range(0,size):
								packetFormat = packetFormat + ' I'
							packetStruct = struct.Struct(packetFormat)
							unpackedData = list(packetStruct.unpack(data))
							dataReceived = []
							pageID = unpackedData[1]
							pageID = struct.unpack('>H',b'\x00' + pageID )[0]
							dataReceived.append(operationCode)
							dataReceived.append(pageID)
							for x in range (3,len(unpackedData)):
								dataReceived.append(unpackedData[x])
							self.pagesToSave.put(dataReceived)

						else:
							print("INVALID OPERATION CODE RECEIVED:" + str(operationCode))

	def classifyPacketsFromMD(self): ## Desempaquetar solo para verificar códigos de operación, en las colas deben guardarse como vienen.
		packetStruct = struct.Struct('1s')
		while True:
			if(self.waitingForMD):
				try:
					data = self.socketMD.recv(700000)
				except socket.error:
					print("Connection lost with MD when waiting a message")  
				if(data):
					#print(data)
					unpackedData = list(packetStruct.unpack(data[:1]))
					operationCode =  struct.unpack('>H',b'\x00' + unpackedData[0] )[0]
					if(operationCode == OK):
						packetStruct = struct.Struct('1s 1s I')
						unpackedData = list(packetStruct.unpack(data[:2]))
						operationCode = struct.unpack('>H',b'\x00' + unpackedData[0])[0]
						pageID = struct.unpack('>H',b'\x00' + unpackedData[1])[0]
						spaceAvailable = unpackedData[2]
						data = {pageID,spaceAvailable}
						self.requestedPages.put(data)
					elif(operationCode == SEND):
						packetFormat = '1s 1s'
						#packetStruct = struct.Struct(packetFormat)
						#unpackedData = list(packetStruct.unpack(data[:8]))
						#size = unpackedData[2]
						for x in range(0,self.pageSize):
							packetFormat = packetFormat + ' I'
						packetStruct = struct.Struct(packetFormat)
						unpackedData = list(packetStruct.unpack(data))
						dataReceived = []
						pageID = unpackedData[1]
						pageID = struct.unpack('>H',b'\x00' + pageID )[0]
						dataReceived.append(pageID)
						for x in range (2,len(unpackedData)):
							dataReceived.append(unpackedData[x])
						self.receiveFromNodes.put(data)

					else:
						print("INVALID OPERATION CODE RECEIVED:" + str(operationCode))

					self.socketMD.close()
					self.waitingForMD = False
				

	def classifyPacketsFromBroadcasts(self):
		client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
		client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
		client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		client.bind(('', 2300))
		while True:
			packetStruct = struct.Struct('1s')
			data = None
			data,adrr = client.recvfrom(700000) #Agregar este conection en la clase
			if(data):
				 #print(data)
				unpackedData = list(packetStruct.unpack(data[:1]))
				operationCode =  struct.unpack('>H',b'\x00' + unpackedData[0] )[0]
				if(operationCode == IAMHERE):
					packetFormat = '1s I'
					packetStruct = struct.Struct(packetFormat)
					unpackedData = list(packetStruct.unpack(data))
					self.newNodes.put((unpackedData[1],adrr[0]))
					self.sendOk(adrr[0])
					

	def sendOk(self,adrr):
		self.socketMD = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
		port = 6000
		connected = False
		while not connected:
			try:  
				self.socketMD.connect( ( adrr, port ) )  
				connected = True  
				#print( "connection successful" )  
			except socket.error:
				print( "no Node" )  #No debería de pasar
				sleep( 2 )
		packetStruct = struct.Struct('1s')
		packet = [bytearray([OK])]
		pageToSend = packetStruct.pack(*(tuple(packet)))
		self.socketMD.send(pageToSend)


					


