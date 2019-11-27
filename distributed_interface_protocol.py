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
		self.pageSize = PAGE_SIZE
		
	def run(self):
		classifier = threading.Thread(target = self.classifyPackets) 
		requester = threading.Thread(target = self.requestPage)
		saver = threading.Thread(target = self.savePage)
		sender = threading.Thread(target=self.sendPage)
		
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
				if( self.ipCurrentNode > -1 )
					### Enviar el paquete (se toma 'pageRequest')
					timeout = time.time() + 10
					okFromDM = False
					packet = []
					while True:
						if(self.ok.empty()):
							if(time.time() > timeout):
								self.pagesToSave.put(pageRequest)
								break
						else:
							okMessage = self.ok.get()
							self.ok.put(okMessage)
							self.okAlreadyRead.release()
							if(okMessage[0] == ERROR):
								print('Error: Could not save page.')
							else:
								okFromDM = True
							break
					if(okayFromDM):
						packetStruct = struct.Struct('1s 1s')
						packet.append(bytearray(OK))
						packet.append(bytearray(okMessage[1]))
						packetStruct.pack( *( tuple(packet) ) )
						####Envíar ok a LM
				
												
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
				if( self.ipCurrentNode > - 1 )
					packetStruct = struct.Struct('1s 1s')
					packet.append(bytearray(OK))
					packet.append(bytearray(pageToRequest))
					packetStruct.pack(*(tuple(packet)))
					### Enviar el paquete solicitud	
		
	def sendPage(self):
		while True: 
			#Proteger con Mutex
			if(not self.receiveFromNodes.empty()):
				self.currentOperation = SEND
				packageReceived = self.receiveFromNodes.get()
				### Enviar el paquete a memoria local tal y como viene
				
		
		
		
				
	def classifyPackets(self): ## Desempaquetar solo para verificar códigos de operación, en las colas deben guardarse como vienen.
