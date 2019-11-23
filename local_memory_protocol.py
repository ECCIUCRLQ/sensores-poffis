import struct
import queue
import threading
import time


## Operation codes.
SAVE_PAGE = 0
REQUEST_PAGE = 1

## Queue size.
QUEUE_SIZE = 10000

## Page size
PAGE_SIZE = 691200

## Data size.
DATA_SIZE = 4

## Number of integers peer page.
DATA_COUNT = PAGE_SIZE // DATA_SIZE

class LocalMemoryProtocol:
	packets = None
	requestedPages = None 
	pagesToSave = None
	ok = None
	pages = None
	okeyAlreadyRead = None
	
	
	def __init__(self):
		self.packets = queue.Queue(QUEUE_SIZE) 
		self.requestedPages = queue.Queue(QUEUE_SIZE) 
		self.pagesToSave = queue.Queue(QUEUE_SIZE) 
		self.ok = queue.Queue(QUEUE_SIZE) 
		self.pages = [None]*(DATA_COUNT) 
		self.okeyAlreadyRead = threading.Semaphore(0)
		
		
	def run(self):
		classifier = threading.Thread(target = self.classifyPackets) 
		requester = threading.Thread(target = self.requestPage)
		saver = threading.Thread(target = self.savePage)
		
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
				packet.append(bytearray(SAVE_PAGE) )
				packet.append(bytearray(pageID))
				packet.append(DATA_COUNT)

				for x in range(0, DATA_COUNT):
					packet.append(page[x])  
				
				packetStruct.pack( * ( tuple(packet) ) )
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
				packet = bytearray(REQUEST_PAGE), bytearray(pageToRequest) 
				packetStruct.pack(packet)
				pageData = []
				### Enviar el paquete solicitud
				
				
	def classifyPackets(self):
		while True:
			### Ver socket para revisar si llegó paquete
				### Si llega un paquete de tipo ok lo mete en la cola de Ok
				### Si no lo mete en la cola de páginas recibidas
	
	
	def unpack():
		
				
					
			
			
