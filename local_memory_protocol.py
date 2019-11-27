import struct
import queue
import threading
import time
import socket

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
DATA_COUNT = 1000

class LocalMemoryProtocol:
	#packets = None
	receivePageFromInterface = None
	requestedPages = None 
	pagesToSave = None
	ok = None
	#pages = None
	okeyAlreadyRead = None
	conn = None
	pageInfo = None
	infoSetInLocalMemory = None
	sendInfoToLocalMemory = None


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
		self.pageInfo = []
		
		
		
	def run(self):
		IPIDLocal = '10.0.2.15' #Cambiar
		port = 6000
		bufferSize = 1
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind((IPIDLocal,port))
		s.listen(1)
		self.conn, addr = s.accept()
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
				packet.append(DATA_COUNT)
				
				for x in range(0, DATA_COUNT):
					packet.append(page[x])  
				#print(packet)
				#print(packetStruct.pack( * ( tuple(packet) ) ) )
				### Enviar el paquete
				timeout = time.time() + 10
				while True:
					if(self.ok.empty()):
						if(time.time() > timeout):
							self.pagesToSave.put(pageRequest)
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
				packetStruct.pack(packet)
				### Enviar el paquete solicitud

	def receivePage(self):
		while True:
			if(not self.receivePageFromInterface.empty()):
				self.pageInfo = [] #Coloca en 0 el número de página y el resto la info
				pageReceived = self.receivePageFromInterface.get()
				#print(pageReceived)
				for x in range (0,len(pageReceived)):
					self.pageInfo.append(pageReceived[x])
				self.sendInfoToLocalMemory.release()
				print(self.pageInfo)
				self.receivePageFromInterface.put(self.pageInfo)
				self.infoSetInLocalMemory.acquire() #A este punto ya está actualizado el nodo y en self.nodeCurrentMemory se colocó el espacio que le queda al nodo
					
				
	def classifyPackets(self):
		while True:
			packetStruct = struct.Struct('1s')
			while True:
				data = self.conn.recv(700000)
				if(data):
					#print(data)
					bufferSize = 700000
					unpackedData = list(packetStruct.unpack(data[:1]))
					operationCode =  struct.unpack('>H',b'\x00' + unpackedData[0] )[0]
					if(operationCode == 3 or operationCode == 4):
						packetStruct = struct.Struct('1s 1s')
						unpackedData = list(packetStruct.unpack(data[:2]))
						typeOk = struct.unpack('>H',b'\x00' + unpackedData[0])[0]
						pageID = struct.unpack('>H',b'\x00' + unpackedData[1])[0]
						data = {typeOk,pageID}
						self.ok.put(data)
					elif(operationCode == 2):
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
						dataReceived.append(pageID)
						for x in range (3,len(unpackedData)):
							dataReceived.append(unpackedData[x])
						self.receivePageFromInterface.put(dataReceived)

					else:
						print("INVALID OPERATION CODE RECEIVED:" + str(operationCode))


						
	
	
		


		
				
					
			
			
