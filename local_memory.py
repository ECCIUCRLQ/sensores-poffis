import csv
import numpy as matrix
import os
from local_memory_protocol import LocalMemoryProtocol 

#Solo pueden haber dos páginas para escribir
MAIN_MEM_PAG_CAP = 4 
#Dos se reservan para escritura 
MAIN_MEM_PAG_WRT = 2
#Dos se reservan para lectura
MAIN_MEM_PAG_RED = 2
#Número arbitrario
SYS_PAG_CAP=100
#3600s*24h*2 ints de datos
PAG_SZE=172800
#Location flag | Reservation Status Flag
#Identifier is given by the position in the array 
INFO_PER_PAGE = 2


MAIN_MEMORY = 0
SECONDARY_MEMORY = 1
NOT_FULL = 0
FULL = 1


class MemoryManager:
	
	def __init__(self):
		#La bandera de localizaión es 0 memoria pricipal y 1 es memoria secundaria
		self.frameTable = matrix.zeros( shape = (SYS_PAG_CAP, INFO_PER_PAGE), dtype = int )  		
		#El más uno es porque cada bloque va tener un identificador con la página que tiene, mapeo directo ya no aplica 
		self.mainMemory = matrix.zeros( shape = (4, PAG_SZE+1), dtype = int )
		#@self.secondaryMemory = [] 
		self.nextId = 0
		self.olderPageIndex = 0
		self.messenger = LocalMemoryProtocol() 
	
	def updateFrameTable(self, pageNumber, location, rsrv_stus):
		self.frameTable[pageNumber][0] = location
		self.frameTable[pageNumber][1] = rsrv_stus
	
	#TODO Acá se hace una competencia para ver donde se va guardar la página nueva, importante para el proceso de que dos espacios son para guardar memoria y el resto es para leer	
	#TODO Este método puede quedar igual solo que a pesar de que hay 4 páginas, se debe solo con las dos primeras, MAIN_MEMORY_PAGE_COUNT debe ser 2.
	def createNewPage(self): 
		if self.nextId < SYS_PAG_CAP: 
			#@newPage = open( str(self.nextId) + ".csv", "a", encoding='utf-8') #Cada página se crea como un archiv de forma num_pag.csv
			
			#This is useful when the MM is not totally assigned 
			if self.nextId < MAIN_MEM_PAG_WRT: 
				self.mainMemory[self.nextId][0]=self.nextId
				self.updateFrameTable(self.nextId, MAIN_MEMORY, NOT_FULL)
				
			
			else:
				#@pageToReplace = self.olderPageIndex % MAIN_MEMORY_PAGE_COUNT #Se busca la poscion de la página más vieja
				pageToReplace = self.search_full_pag()
				self.sendToSecondaryMemory(pageToReplace) #Se envía a memoria secundaria
				self.updateFrameTable(self.mainMemory[pageIndex][0], SECONDARY_MEMORY, FULL)
				self.mainMemory[pageToReplace][0] = self.nextId
				self.updateFrameTable(self.nextId, MAIN_MEMORY, NOT_FULL)
				#@self.mainMemory[pageToReplace] = newPage #Se pone el buffer en la memoria principal 

			#@self.updateFrameTable(self.nextId, self.olderPageIndex % MAIN_MEMORY_PAGE_COUNT , MAIN_MEMORY)
			
			self.nextId += 1
			#@self.olderPageIndex += 1
			return self.nextId-1
		else: 
			return -1
			
	#Search for a full page in MM 
	def search_full_pag(self):
		for memIndx in range(MAIN_MEM_PAG_WRT):
			pagNumber = self.mainMemory[memIndx][0]
			if self.frameTable[pagNumber][1] == FULL:
				return memIndx
		
		return -1		
		
				
		
	
	#Cuando se lee de memoria secundaria no importa porque nunca hay que sobre-escribir
	#TODO cuando se lee una página decidir si se actuliza la tabla, porque luego es difícil consegir la dirección en memoria secundaria orginal. Es mejor que no, solo el bit de la bandera, pero  		eso afecta como se direcciona en la memoria secundaria ya que las direcciones secundarias son diferentes a los índices de memoria principal
	def sendToSecondaryMemory(self, pageToReplace):
		self.messenger.pagesToSave.put(self.mainMemory[pageToReplace])
		#Leer de la cola, se cambia por un semáforo
		#@self.secondaryMemory.append( self.mainMemory[pageToReplace] ) #se pone el buffer en el arreglo de memoria secundaria
		self.updateFrameTable(pageToReplace, len(self.secondaryMemory) - 1, SECONDARY_MEMORY) #La dirección en memoria secundaria es el tamaño del buffer, esa dirección nunca cambia luego
		
	#Since straight targeting is no loger used this method is needed to find the position of a page in MM 
	def get_MM_index(self, pageNumber):
		for memIndx in range(MAIN_MEM_PAG_WRT):
			if self.mainMemory[mem_indx][0] == pageNumber:
				return memIndx
	
	#Since no page can be sent to secondary memory in a state different from full, page to be written must be always in main memory	
	def writePage(self, pageNumber, date, data, offset): º
		if self.frameTable[pageNumber][0] == MAIN_MEMORY: # Si la página está en memoria principal.
			postion = self.get_MM_index(pageNumber)
			self.mainMemory[position][offset]=date
			self.mainMemory[position][offset+1]=date
			
		else: 
			print("Fail to write")
			
	def doSwap(self, pageMainMem, pageSecondMem, mainMemIndex, secondMemIndex):
		temp = self.mainMemory[mainMemIndex]
		self.mainMemory[mainMemIndex] = self.secondaryMemory[secondMemIndex]
		self.secondaryMemory[secondMemIndex] = temp
		self.updateFrameTable(pageMainMem, secondMemIndex, SECONDARY_MEMORY)
		self.updateFrameTable(pageSecondMem, mainMemIndex, MAIN_MEMORY)
	
		
	#@def sendPageToInterface(self, pageNumber): # Enviar página de memoria principal a interfaz
	def requestPage(self, pageNumber):
		
		if self.frameTable[pageNumber][0] == MAIN_MEMORY:  #Se comprueba si está en la memoria principal
			postion = self.get_MM_index(pageNumber)
			dataBuffer = main_memory[position]
			
			#@pageName = self.mainMemory[ self.frameTable[pageNumber][0] ].name #name es el nombre del archivo de donde está la página
			#@page = int( os.path.basename(pageName).rsplit('.',1)[0] )
			#@self.mainMemory[ self.frameTable[pageNumber][0] ].seek(0)
		else:
			
			pageName = self.secondaryMemory[ self.frameTable[pageNumber][0] ].name
			page = int( os.path.basename(pageName).rsplit('.',1)[0] )
			self.secondaryMemory[ self.frameTable[pageNumber][0] ].seek(0)
		
		# Posiciones pares contienen la fecha e impares el dato.
		csv_file =  open( str(page) + ".csv", 'r' ) 
		csvReader = csv.reader(csv_file)
		for currentLine in csvReader:
			dataBuffer.append(currentLine[0])
			dataBuffer.append(currentLine[1])
		return dataBuffer

"""kappa = MemoryManager()
kappa.createNewPage()
print(kappa.frameTable)
print()
kappa.createNewPage()
print(kappa.frameTable)
print()
kappa.createNewPage()
print(kappa.frameTable)
print()
kappa.createNewPage()
print(kappa.frameTable)
print()
kappa.createNewPage()
print(kappa.frameTable)
print()
kappa.writePage(0,1571853632, 777, 0)
kappa.writePage(0,1571853633, 3154,0)
print( kappa.sendPageToInterface(0) )
kappa.writePage(0,1571853634,777,0)"""
