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


## Queue size.
QUEUE_SIZE = 10000

## Page size
PAGE_SIZE = 691200

## Data size.
DATA_SIZE = 4

## Number of integers peer page.
#DATA_COUNT = PAGE_SIZE // DATA_SIZE
DATA_COUNT = 10

class LocalMemoryProtocol:
	#packets = None
	receivePageFromInterface = None
	requestedPages = None
	pagesToSave = None
	ok = None
	#pages = None
	okeyAlreadyRead = None
	socket = None
	pageInfo = None
	infoSetInLocalMemory = None
	sendInfoToLocalMemory = None
	waitingAnswerFromID = None
	kappa = None

	def __init__(self):
		#self.packets = queue.Queue(QUEUE_SIZE)
		self.requestedPages = queue.Queue(QUEUE_SIZE)
		self.pagesToSave = queue.Queue(QUEUE_SIZE)
		self.ok = queue.Queue(QUEUE_SIZE)
		self.receivePageFromInterface = queue.Queue(QUEUE_SIZE)
		#self.pages = [None]*(DATA_COUNT)
		self.okeyAlreadyRead = threading.Semaphore(0)
		self.sendInfoToLocalMemory = threading.Semaphore(0)
		self.infoSetInLocalMemory = threading.Semaphore(0)
		self.kappa = threading.Semaphore(1)
		self.pageInfo = []
		self.socket = None
		self.waitingAnswerFromID = False



	def run(self):

		classifier = threading.Thread(target = self.classifyPackets)
		requester = threading.Thread(target = self.requestPage)
		saver = threading.Thread(target = self.savePage)
		receiver = threading.Thread(target= self.receivePage)
		classifier.start()
		requester.start()
		saver.start()
		receiver.start()



	def savePage(self):
		while True:
			if(self.pagesToSave.qsize() > 1):
				print ("uff")
			if( not self.pagesToSave.empty() ):
				pageRequest = self.pagesToSave.get()
				pageID = pageRequest[0]
				page = [None] * (DATA_COUNT)
				packet = []
				for x in range(1, DATA_COUNT + 1):
					page[x-1] = pageRequest[x]
				packetFormat = '1s 1s I '
				for x in range(0, DATA_COUNT):
					packetFormat = packetFormat + 'I'

				packetStruct = struct.Struct(packetFormat)
				packet.append(bytearray([SAVE_PAGE]) )
				packet.append(bytearray([pageID]))
				packet.append(DATA_COUNT*DATA_SIZE)

				for x in range(0, DATA_COUNT):
					packet.append(page[x])
				#print(packet)
				#print(packetStruct.pack( * ( tuple(packet) ) ) )
				#Crear Socket
				self.kappa.acquire()
				self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				IPIDLocal = '192.168.1.30' #Cambiar
				port = 6021
				connected = False
				while not connected:
					try:
						self.socket.connect( ( IPIDLocal, port ) )
						connected = True
						#print( "connection successful" )
					except socket.error:
						print( "no ID" )
						sleep( 2 )
				packetData = packetStruct.pack( * ( tuple(packet) ) )
				self.socket.send(packetData)
				self.waitingAnswerFromID = True
				timeout = time.time() + 10
				while True:
					if(self.ok.empty()):
						if(time.time() > timeout):
							self.pagesToSave.put(pageRequest)
							self.waitingAnswerFromID = False
							break
					else:
						okMessage = self.ok.get()
						self.okeyAlreadyRead.release()
						if(okMessage[0] == ERROR):
							print('Error: Could not save page.')
						break

	def requestPage(self):
		while True:
			if( not self.requestedPages.empty() ):
				pageToRequest = self.requestedPages.get()
				packetStruct = struct.Struct('1s 1s')
				packet = bytearray([REQUEST_PAGE]), bytearray([pageToRequest])
				packetData = packetStruct.pack(*(packet))
				#Crear Socket
				self.kappa.acquire()
				self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				IPIDLocal = '192.168.1.30' #Cambiar
				port = 6021
				connected = False
				while not connected:
					try:
						self.socket.connect( ( IPIDLocal, port ) )
						connected = True
						#print( "connection successful" )
					except socket.error:
						print( "no ID" )
						sleep( 2 )
				### Enviar el paquete solicitud
				self.socket.send(packetData)
				self.waitingAnswerFromID = True

	def receivePage(self):
		while True:
			if(not self.receivePageFromInterface.empty()):
				self.pageInfo = [] #Coloca en 0 el número de página y el resto la info
				pageReceived = self.receivePageFromInterface.get()
				#print(pageReceived)
				for x in range (0,len(pageReceived)):
					self.pageInfo.append(pageReceived[x])
				self.sendInfoToLocalMemory.release()
				#print(self.pageInfo)
				self.receivePageFromInterface.put(self.pageInfo)
				self.infoSetInLocalMemory.acquire() #A este punto ya está actualizado el nodo y en self.nodeCurrentMemory se colocó el espacio que le queda al nodo


	def classifyPackets(self):
		while True:
			if(self.waitingAnswerFromID):
				while(True):
					try:
						data = self.socket.recvfrom(700000)[0]
						#print(data)
						break
					except socket.error:
						print("Connection lost with ID when waiting a message")
						sleep(1)
						data = False
				if(data):
					#print(data)
					packetStruct = struct.Struct('1s')
					unpackedData = list(packetStruct.unpack(data[:1]))
					operationCode =  struct.unpack('>H',b'\x00' + unpackedData[0] )[0]
					if(operationCode == 2 or operationCode == 4):
						packetStruct = struct.Struct('1s 1s')
						unpackedData = list(packetStruct.unpack(data[:2]))
						typeOk = struct.unpack('>H',b'\x00' + unpackedData[0])[0]
						pageID = struct.unpack('>H',b'\x00' + unpackedData[1])[0]
						data = []
						data.append(typeOk)
						data.append(pageID)
						self.ok.put(data)
					elif(operationCode == 3):
						packetFormat = '1s 1s'
						#size = unpackedData[2]
						for x in range(0,DATA_COUNT):
							packetFormat = packetFormat + ' I'
						packetStruct = struct.Struct(packetFormat)
						unpackedData = list(packetStruct.unpack(data))
						dataReceived = []
						pageID = unpackedData[1]
						pageID = struct.unpack('>H',b'\x00' + pageID )[0]
						dataReceived.append(pageID)
						for x in range (2,len(unpackedData)):
							dataReceived.append(unpackedData[x])
						self.receivePageFromInterface.put(dataReceived)
					else:
						print("INVALID OPERATION CODE RECEIVED:" + str(operationCode))
					self.waitingAnswerFromID = False
					self.socket.close()
					self.kappa.release()


'''kappa = LocalMemoryProtocol()
kappa.run()
kappa2 = []
for x in range (0,DATA_COUNT+1):
	kappa2.append(x)
kappa.pagesToSave.put(kappa2)
while(True):
	if(not kappa.ok.empty()):
		kappa2[0] = 1
		kappa.requestedPages.put(0)
		break
while(True):
	if(not kappa.receivePageFromInterface.empty()):
		print(kappa.receivePageFromInterface.get())
		break
'''
