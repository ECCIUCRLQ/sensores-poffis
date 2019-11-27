import struct
import queue
import threading
import time

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
DATA_COUNT = PAGE_SIZE // DATA_SIZE


class DistributedInterfaceProtocol:
	packets = None
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
	
	
	def __init__(self):
		self.packets = queue.Queue(QUEUE_SIZE) 
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
		
	def run(self):
		classifier = threading.Thread(target = self.classifyPackets) 
		requester = threading.Thread(target = self.requestPage)
		saver = threading.Thread(target = self.savePage)
		
	def savePage(self):	
		## Proteger con mutex.
		while True:
			if( not self.pagesToSave.empty() ):
				pageRequest =  self.pagesToSave.get()
				## Desempaqueta
				### Coloca en la variable de tamaño solicitado según lo que desempaqueto.
				self.currentOperation = SAVE_PAGE
				### Esperar que ID activa me diga la IP del nodo en el que hay que guardar.
				self.idTellMeTheIp.release()
				### ID activa avisa que ya nos dio la IP.
				self.iAlreadyKnowIp.acquire()
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
						self.ok.put(okMesage)
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
				if( not self.requestedPages.empty() ):
					pageToRequest = self.requestedPages.get()
					self.currentOperation = REQUEST_PAGE
					self.idTellMeTheIp.release()
					self.iAlreadyKnowIp.acquire()
					### Enviar el paquete solicitud	
		
	def sendPage(self): 
		self.currentOperation = SEND
		
		
				
	def classifyPackets(self): ## Desempaquetar solo para verificar códigos de operación, en las colas deben guardarse como vienen.
	
