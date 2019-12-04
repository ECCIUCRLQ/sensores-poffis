import struct
import queue
import threading
import time
import socket
from time import sleep
import ipaddress
import uuid
import netifaces as ni
from subprocess import call

## Operation codes. MD
SAVE_PAGE = 0
REQUEST_PAGE = 1
OK = 2
SEND = 3
ERROR = 4
IAMHERE = 5

## Operation codes. ID
IWANTTOBE = 0
IAMACTIVE = 1
KEEPALIVE = 2

## Queue size.
QUEUE_SIZE = 10000

## Page size
PAGE_SIZE = 691200

## Data size.
DATA_SIZE = 4

## Number of integers peer page.
DATA_COUNT = PAGE_SIZE // DATA_SIZE

## Direccion IP 
IDIP  = "192.168.1.30"

## Mascara de red
NETMASK = "255.255.255.0"


class DistributedInterfaceProtocol:
	MACAdress = None
	iWantToBeQueue = None
	iAmChampionQueue = None
	keepAliveQueue = None
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
	kappa = None
	kappa2 = None
	iAmIDActive = None

	def __init__(self):
		self.MACAdress = uuid.getnode()
		self.iWantToBeQueue = queue.Queue(QUEUE_SIZE)
		self.iAmChampionQueue = queue.Queue(QUEUE_SIZE)
		self.keepAliveQueue = queue.Queue(QUEUE_SIZE)
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
		self.kappa = threading.Semaphore(1)
		self.kappa2 = threading.Semaphore(1)
		self.currentOperation = -1
		self.pageId = -1
		self.pageSize = 0
		self.socketML = None
		self.socketMD = None
		self.waitingForMD = False
		self.waitingToSendToML = False
		self.sizeInNode = None
		self.iAmIDActive = False

	def run(self):
		classifierBroadcastID = threading.Thread(target = self.classifyPacketsFromBroadcastsFromID)
		#Aqui va la pelea entre interfaces y se queda aqui mientras no sea activo
		classifierBroadcastID.start()
		championsResult,tablesReceived = self.champions(True)
		if(championsResult):
			self.runActive()
		else:
			self.runPasive()
		return tablesReceived

	def runActive(self):
		classifierML = threading.Thread(target = self.classifyPacketsFromML)
		classifierMD = threading.Thread(target = self.classifyPacketsFromMD)
		classifierBroadcastMD = threading.Thread(target = self.classifyPacketsFromBroadcastsFromMD)
		requester = threading.Thread(target = self.requestPage)
		saver = threading.Thread(target = self.savePage)
		sender = threading.Thread(target=self.sendPage)
		classifierML.start()
		classifierMD.start()
		saver.start()
		sender.start()
		requester.start()
		classifierBroadcastMD.start()
		self.iAmIDActive = True

	def runPasive(self):
		self.iAmIDActive = False

	def champions(self,firstTime):
		tablesReceived = None
		round = 0
		alive = True
		if(not firstTime):
			round = 3
		#Limpiar cola de yo quiero ser campeon
		self.clearChampionshipQueues()
		#Mandar broadcast de quiero ser campeón con mi ronda y esperar mensajes de los otros
		self.sendIWantToBeChampion(round)
		#Crear timer de 3 segundos simbolizando la champions -> while True
		timeout = time.time() + 3
		while(time.time() < timeout and alive):
			#Si me llega uno de quiero ser campeon
			if(not self.iWantToBeQueue.empty()):
				messageFromOtherID = self.iWantToBeQueue.get()
				# Compara la ronda, si es igual si juega
				if(messageFromOtherID[1] == round):
					print("llegó un competidor con ronda:" + str(messageFromOtherID[1]))
					#Si el mayor el MAC entonces pierdo
					if( messageFromOtherID[0] > self.MACAdress ):
						print ("Perdí contra otra MAC, mi MAC es: " + str(self.MACAdress) + " y la que me ganó es: " + str(messageFromOtherID[0]))
						alive = False
					#Si es menor entonces le suma uno a ronda y envía yo quiero ser campeón con la ronda
					elif( messageFromOtherID[0] < self.MACAdress):
						print ("Gané contra otra MAC, mi MAC es: " + str(self.MACAdress) + " y la que perdió es: " + str(messageFromOtherID[0]))
						round = round + 1
						self.sendIWantToBeChampion(round)
					#Si son iguales hay error
					else:
						print ("Error: Champions: Two interfaces with the same MAC address")
					
				# Si es menor la ronda lo ignoro
				elif(messageFromOtherID[1] < round):
					print("llegó un competidor con ronda menor: "+ str(messageFromOtherID[1]) + " lo ignoro porque mi ronda es: " + str(round))
				# Si la ronda es mayor pierdo 
				elif(messageFromOtherID[1] > round):
					print("llegó un competidor con ronda mayor: "+ str(messageFromOtherID[1]) + " perdí :( porque mi ronda es:" + str(round)) 
					alive = False
			#Si me llega un soy compeón
			if(not self.iAmChampionQueue.empty()):
				#RECORDAR AGARRAR LOS DATOS PARA LAS TABLAS	
				tablesReceived = self.iAmChampionQueue.get()
				self.iAmChampionQueue.put(tablesReceived)
				#Piedo automáticamente
				alive = False

		#Si estoy vivo enviar soy campeón y esperar un segundo por si llega otro soy campeón
		if(alive):
			print("gané")
			self.sendIAmChampion(0,0,0,0)
			#Si llega otro soy campeón envío un quiero ser campeón
			timeout = time.time() + 1
			while(time.time() < timeout):
				if(not self.iAmChampionQueue.empty()):
						kappa = self.iAmChampionQueue.get()
						print("Me toca darme de putazos")
		else:
			print("perdí")
			#Quedarme esperando el IAmChampion por 5 segundos
			timeout = time.time() + 5
			thereIsAWinner = False
			while(time.time() < timeout):
				if(not self.iAmChampionQueue.empty()):
					tablesReceived = self.iAmChampionQueue.get()
					thereIsAWinner = True
			if(not thereIsAWinner):
				return self.champions(firstTime)
			
		return alive,tablesReceived
		
	def sendIWantToBeChampion(self, round):
		bytesMACAdrress = self.MACAdress.to_bytes(6,byteorder = "little")
		packet = (bytearray([IWANTTOBE]),bytearray([bytesMACAdrress[0],bytesMACAdrress[1],bytesMACAdrress[2],bytesMACAdrress[3],bytesMACAdrress[4],bytesMACAdrress[5]]),bytearray([round]))
		print(packet)
		packetStruct = struct.Struct('=1s 6s 1s')
		packetInfo = packetStruct.pack(*(packet))
		server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# Permitir broadcast
		server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		server.sendto(packetInfo, ('192.168.1.255', 6667))

	def sendIAmChampion(self, row1, row2, rowdata1, rowdata2):
		packetFormat = '=1s 1s 1s'
		packet = []
		packet.append(bytearray([IAMACTIVE]))
		packet.append(bytearray([row1]))
		packet.append(bytearray([row2]))
		for x in range (0,row1):
			packetFormat = packetFormat + '1s 1s'
			packet.append(bytearray([rowdata1[x][0]]))
			packet.append(bytearray([rowdata1[x][1]]))

		for x in range (0,row2):
			packetFormat = packetFormat + '1s I I'
			packet.append(bytearray([rowdata2[x][0]]))
			packet.append(int(ipaddress.IPv4Address(rowdata2[x][1])))
			packet.append(rowdata2[x][2])

		packetStruct = struct.Struct(packetFormat)

		packetInfo = packetStruct.pack(*(packet))
		server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# Permitir broadcast
		server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		server.sendto(packetInfo, ('192.168.1.255', 6667))
	
	def clearChampionshipQueues(self):
		while not self.iWantToBeQueue.empty():
			self.iWantToBeQueue.get()
		while not self.iAmChampionQueue.empty():
			self.iAmChampionQueue.get()

	def sendKeepAlive(self, pageTable, changesInPageTable, nodeTable, changesInNodeTable):
		packetFormat = '=1s 1s 1s'
		packet = []
		packet.append(bytearray([KEEPALIVE]))
		numberOfChangesInPageTable = 0
		numberOfChangesInNodeTable = 0

		changesInPageTableData = []
		changesInNodeTableData = []

		for x in range (0,len(changesInPageTable)):
			if(changesInPageTable[x]):
				numberOfChangesInPageTable =  numberOfChangesInPageTable + 1
				changesInPageTableData.append((pageTable[x][0],pageTable[x][1]))

		for x in range (0,len(changesInNodeTable)):
			if(changesInNodeTable[x]):
				numberOfChangesInNodeTable =  numberOfChangesInNodeTable + 1
				changesInNodeTableData.append((nodeTable[x][0],nodeTable[x][1],nodeTable[x][2]))

		packet.append(bytearray([numberOfChangesInPageTable]))
		packet.append(bytearray([numberOfChangesInNodeTable]))

		for x in range (0,len(changesInPageTableData)):
			packetFormat = packetFormat + '1s 1s'
			packet.append(bytearray([changesInPageTableData[x][0]]))
			packet.append(bytearray([changesInPageTableData[x][1]]))

		for x in range (0,len(changesInNodeTableData)):
			packetFormat = packetFormat + '1s I I'
			packet.append(bytearray([changesInNodeTableData[x][0]]))
			packet.append( int(ipaddress.IPv4Address(changesInNodeTableData[x][1]) ) )
			packet.append(changesInNodeTableData[x][2])

		packetStruct = struct.Struct(packetFormat)
		packetData = packetStruct.pack(*(tuple(packet)))
		print('Paquete Keep Alive: ' + str(packet) )

		server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# Permitir broadcast
		server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		server.sendto(packetData, ('192.168.1.255', 6667))

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
				packetFormat = '=1s 1s I'

				for x in range (0,self.pageSize//4):
					packetFormat = packetFormat + ' I'
				packetStruct = struct.Struct(packetFormat)
				packet = []
				packet.append( bytearray([pageRequest[0]]))
				packet.append( bytearray([pageRequest[1]]))
				packet.append( pageRequest[2])
				for x in range (0,self.pageSize//4):
					packet.append(pageRequest[x+3])
				pageToSend = packetStruct.pack(*(tuple(packet)))
				self.kappa2.acquire()
				self.socketMD = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				port = 6000
				connected = False
				while not connected:
					try:
						self.socketMD.connect( ( self.ipCurrentNode, port ) )
						connected = True
					except socket.error:
						print( "Error: savePage(): Could not establish connection with node")
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
						okFromDM = True
						break
				if(okFromDM):
					packetStruct = struct.Struct('=1s 1s')
					packet.append(bytearray([OK]))
					packet.append(bytearray([okMessage[0]]))
					self.sizeInNode = okMessage[1]
					sendInfo = packetStruct.pack( *( tuple(packet) ) )
					self.socketML.send(sendInfo)
					self.socketML.close()
					self.kappa.release()
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
				#if( self.ipCurrentNode > - 1 ):
				packetStruct = struct.Struct('=1s 1s')
				packet.append(bytearray([REQUEST_PAGE]))
				packet.append(bytearray([pageToRequest]))
				packetData = packetStruct.pack(*(tuple(packet)))
				self.socketMD = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				port = 6000
				connected = False
				while not connected:
					try:
						self.socketMD.connect( ( self.ipCurrentNode, port ) )
						connected = True
					except socket.error:
						print( "Error: requestPage(): Could not establish connection with node")
						sleep( 2 )
				self.socketMD.send(packetData)
				self.kappa2.acquire()
				self.waitingForMD = True

	def sendPage(self):
		while True:
			#Proteger con Mutex
			if(not self.receiveFromNodes.empty()):
				self.currentOperation = SEND
				packageReceived = self.receiveFromNodes.get()
				self.socketML.send(packageReceived)
				self.socketML.close()
				self.kappa.release()
				self.waitingToSendToML = False

	def classifyPacketsFromML(self): ## Desempaquetar solo para verificar códigos de operación, en las colas deben guardarse como vienen.	
		while True:
			packetStruct = struct.Struct('=1s')
			while True:
				if(not self.waitingToSendToML):
					self.kappa.acquire()
					call( [ "sudo", "ip", "addr", "flush", "dev", "eno1"]  )
					call( ["ip", "a", "add", IDIP + "/" + NETMASK, "dev", "eno1"]  )
					s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					host = IDIP 
					port = 6021
					s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
					s.bind( ( host, port ) )
					s.listen()
					self.socketML,addr = s.accept()
					data = self.socketML.recv(700000)
					if(data):
						self.waitingToSendToML = True
						packetStruct = struct.Struct('=1s')
						unpackedData = list(packetStruct.unpack(data[:1]))
						operationCode =  struct.unpack('>H',b'\x00' + unpackedData[0] )[0]
						if(operationCode == REQUEST_PAGE):
							packetStruct = struct.Struct('=1s 1s')
							unpackedData = list(packetStruct.unpack(data[:2]))
							operationCode = struct.unpack('>H',b'\x00' + unpackedData[0])[0]
							pageID = struct.unpack('>H',b'\x00' + unpackedData[1])[0]
							data = pageID
							self.requestedPages.put(data)
							print('Distributed Interface: Request to bring page #' + str(pageID))
						elif(operationCode == SAVE_PAGE):
							packetFormat = '=1s 1s I'
							packetStruct = struct.Struct(packetFormat)
							unpackedData = list(packetStruct.unpack(data[:6]))
							size = unpackedData[2] //4
							for x in range(0,size):
								packetFormat = packetFormat + ' I'
							packetStruct = struct.Struct(packetFormat)
							unpackedData = list(packetStruct.unpack(data))
							dataReceived = []
							pageID = unpackedData[1]
							pageID = struct.unpack('>H',b'\x00' + pageID )[0]
							dataReceived.append(operationCode)
							dataReceived.append(pageID)
							dataReceived.append(size*4)
							for x in range (3,len(unpackedData)):
								dataReceived.append(unpackedData[x])
							self.pagesToSave.put(dataReceived)
							print('Distributed Interface: Request to save page #' + str(pageID))

						else:
							print("Error: Invalid operation code received (" + str(operationCode) + ")")

	def classifyPacketsFromMD(self): 
		while True:
			if(self.waitingForMD):
				try:
					data = self.socketMD.recv(700000)
				except socket.error:
					print("Error: Connection lost with MD when waiting a message")
				if(data):
					packetStruct = struct.Struct('=1s')
					unpackedData = list(packetStruct.unpack(data[:1]))
					operationCode =  struct.unpack('>H',b'\x00' + unpackedData[0] )[0]
					if(operationCode == OK):
						packetStruct = struct.Struct('=1s 1s I')
						unpackedData = list(packetStruct.unpack(data[:6]))
						operationCode = struct.unpack('>H',b'\x00' + unpackedData[0])[0]
						pageID = struct.unpack('>H',b'\x00' + unpackedData[1])[0]
						spaceAvailable = unpackedData[2]
						data = []
						print(pageID)
						data.append(pageID)
						data.append(spaceAvailable)
						self.ok.put(data)
					elif(operationCode == SEND):
						packetFormat = '=1s 1s'
						for x in range(0,self.pageSize//4):
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
						print("Error: Invalid operation code received (" + str(operationCode) + ")")

					self.socketMD.close()
					self.kappa2.release()
					self.waitingForMD = False


	def classifyPacketsFromBroadcastsFromMD(self):
		client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
		client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
		client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		client.bind(('', 2300))
		while True:
			packetStruct = struct.Struct('=1s')
			data = None
			data,adrr = client.recvfrom(700000) #Agregar este conection en la clase
			if(data):
				unpackedData = list(packetStruct.unpack(data[:1]))
				operationCode =  struct.unpack('>H',b'\x00' + unpackedData[0] )[0]
				if(operationCode == IAMHERE):
					packetFormat = '=1s I'
					packetStruct = struct.Struct(packetFormat)
					unpackedData = list(packetStruct.unpack(data))
					self.newNodes.put((unpackedData[1],adrr[0]))
					self.sendOk(adrr[0])
		
	def classifyPacketsFromBroadcastsFromID(self):
		client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
		client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
		client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		client.bind(('', 6667)) #Cambiar puerto
		while True:
			packetStruct = struct.Struct('=1s')
			data = None
			data,adrr = client.recvfrom(700000) #Agregar este conection en la clase
			kappa = adrr
			ip = ni.ifaddresses("eno1")[ni.AF_INET][0]['addr'] #USAR EN LA U
			#ip = ni.ifaddresses("enp0s3")[ni.AF_INET][0]['addr'] #USAR EN LAS MÁQUINAS VIRTUALES
			if(data and not (adrr[0] == ip)):
				unpackedData = list(packetStruct.unpack(data[:1]))
				operationCode =  struct.unpack('>H',b'\x00' + unpackedData[0] )[0]
				if(operationCode == IWANTTOBE):
					packetFormat = '=1s 6s 1s'
					packetStruct = struct.Struct(packetFormat)
					unpackedData = list(packetStruct.unpack(data))
					receivedMACAddress = int.from_bytes(unpackedData[1],byteorder = "little",signed='False')
					round = struct.unpack('>H',b'\x00' + unpackedData[2] )[0]
					# Meter en la cola -> (receivedMACAddress , round)
					if(not (receivedMACAddress == self.MACAdress)):
						self.iWantToBeQueue.put((receivedMACAddress,round))


				if(operationCode== IAMACTIVE):
					packetFormat = '=1s 1s 1s'
					packetStruct = struct.Struct(packetFormat)
					unpackedData = list(packetStruct.unpack(data[:3]))
					pageTableSize = struct.unpack('>H',b'\x00' + unpackedData[1] )[0]
					nodeTableSize = struct.unpack('>H',b'\x00' + unpackedData[2] )[0]
					for x in range(0,pageTableSize):
						packetFormat = packetFormat + '1s 1s'
					for x in range(0,nodeTableSize):
						packetFormat = packetFormat + '1s I I'
					packetStruct = struct.Struct(packetFormat)
					unpackedData = list(packetStruct.unpack(data))
					pageTableInfo = []
					nodeTableInfo = []
					nodeTableStart = 3
					for x in range (3,((pageTableSize*2)+3),2):
						pageID = struct.unpack('>H',b'\x00' + unpackedData[x] )[0]
						nodeID = struct.unpack('>H',b'\x00' + unpackedData[x+1] )[0]
						pageTableInfo.append((pageID,nodeID))
						nodeTableStart = x+2
					for x in range(nodeTableStart,nodeTableStart + (nodeTableSize * 3),3):
						nodeID =  struct.unpack('>H',b'\x00' + unpackedData[x] )[0]
						IP = str(ipaddress.IPv4Address(unpackedData[x+1]))
						spaceAvailable = unpackedData[x+2]
						nodeTableInfo.append((nodeID,IP,spaceAvailable))
					#Meter en cola de IAMACTIVE -> {tamaño tabla de páginas, tamaño tabla de nodos, tabla de pagina, tabla de nodo}
					datalist = []
					datalist.append(pageTableInfo)
					datalist.append(nodeTableInfo)
					self.iAmChampionQueue.put(datalist)


				if(operationCode == KEEPALIVE):
					packetFormat = '=1s 1s 1s'
					packetStruct = struct.Struct(packetFormat)
					unpackedData = list(packetStruct.unpack(data[:3]))
					pageTableSize = struct.unpack('>H',b'\x00' + unpackedData[1] )[0]
					nodeTableSize = struct.unpack('>H',b'\x00' + unpackedData[2] )[0]
					for x in range(0,pageTableSize):
						packetFormat = packetFormat + '1s 1s'
					for x in range(0,nodeTableSize):
						packetFormat = packetFormat + '1s I I'
					packetStruct = struct.Struct(packetFormat)
					unpackedData = list(packetStruct.unpack(data))
					pageTableInfo = []
					nodeTableInfo = []
					nodeTableStart = 3
					for x in range (3,((pageTableSize*2)+3),2):
						pageID = struct.unpack('>H',b'\x00' + unpackedData[x] )[0]
						nodeID = struct.unpack('>H',b'\x00' + unpackedData[x+1] )[0]
						pageTableInfo.append((pageID,nodeID))
						nodeTableStart = x+2
					for x in range(nodeTableStart,nodeTableStart + (nodeTableSize * 3),3):
						nodeID =  struct.unpack('>H',b'\x00' + unpackedData[x] )[0]
						IP = str(ipaddress.IPv4Address(unpackedData[x+1]))
						spaceAvailable = unpackedData[x+2]
						nodeTableInfo.append((nodeID,IP,spaceAvailable))

					#Meter en cola de KEEPALIVE -> {tabla de pagina, tabla de nodo}
					datalist = []
					datalist.append(pageTableInfo)
					datalist.append(nodeTableInfo)
					self.keepAliveQueue.put(datalist)


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
		packetStruct = struct.Struct('=1s')
		packet = [bytearray([OK])]
		pageToSend = packetStruct.pack(*(tuple(packet)))
		self.socketMD.send(pageToSend)
