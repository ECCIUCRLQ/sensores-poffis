import csv
import numpy as matrix
import os

MAX_PAGE_COUNT = 10
MAIN_MEMORY_PAGE_COUNT = 10
INFO_PER_PAGE = 2
MAIN_MEMORY = 0
SECONDARY_MEMORY = 1


class MemoryManager:
	
	def __init__(self):
		self.frameTable = matrix.zeros( shape = (MAX_PAGE_COUNT, INFO_PER_PAGE), dtype = int )  #Cada linea de la matriz contiene Dirección física | Bandera de localizacion |  
		#La bandera de localizaión es 0 memoria pricipal y 1 es memoria secundaria		
		self.mainMemory = []
		self.secondaryMemory = [] 
		self.lastPageCreated = -1
		self.olderPageIndex = 0 
	
	def updateFrameTable(self, pageNumber, physicalAddress, secondaryMemory):
		self.frameTable[pageNumber][0] = physicalAddress
		self.frameTable[pageNumber][1] = secondaryMemory
	
	#TODO Acá se hace una competencia para ver donde se va guardar la página nueva, importante para el proceso de que dos espacios son para guardar memoria y el resto es para leer	
	#TODO Este método puede quedar igual solo que a pesar de que hay 4 páginas, se debe solo con las dos primeras, MAIN_MEMORY_PAGE_COUNT debe ser 2.
	def createNewPage(self): 
		if self.lastPageCreated < MAX_PAGE_COUNT: 
			self.lastPageCreated += 1 
			newPage = open( str(self.lastPageCreated) + ".csv", "a", encoding='utf-8') #Cada página se crea como un archiv de forma num_pag.csv
			
			if self.olderPageIndex < MAIN_MEMORY_PAGE_COUNT: #La página se agrega a memoria principal si hay campo, ojo lo que se agrega es el buffer, se hace con append porque aún no 				#existe la posición 
				self.mainMemory.append(newPage)
				
			else:
				pageToReplace = self.olderPageIndex % MAIN_MEMORY_PAGE_COUNT #Se busca la poscion de la página más vieja
				self.sentToSecondaryMemory(pageToReplace) #Se envía a memoria secundaria
				self.mainMemory[pageToReplace] = newPage #Se pone el buffer en la memoria principal 

			self.updateFrameTable(self.lastPageCreated, self.olderPageIndex % MAIN_MEMORY_PAGE_COUNT , MAIN_MEMORY)
			
				
			self.olderPageIndex += 1
			return self.lastPageCreated
		else: 
			return -1
	
	#Cuando se lee de memoria secundaria no importa porque nunca hay que sobre-escribir
	#TODO cuando se lee una página decidir si se actuliza la tabla, porque luego es difícil consegir la dirección en memoria secundaria orginal. Es mejor que no, solo el bit de la bandera, pero  		eso afecta como se direcciona en la memoria secundaria ya que las direcciones secundarias son diferentes a los índices de memoria principal
	def sentToSecondaryMemory(self, pageToReplace):
		self.secondaryMemory.append( self.mainMemory[pageToReplace] ) #se pone el buffer en el arreglo de memoria secundaria
		self.updateFrameTable(pageToReplace, len(self.secondaryMemory) - 1, SECONDARY_MEMORY) #La dirección en memoria secundaria es el tamaño del buffer, esa dirección nunca cambia luego
		
	def writePage(self, pageNumber, date, data, offset): 
		packageInfo = [date,data]
		if self.frameTable[pageNumber][1] == 0: # Si la página está en memoria principal.
			pageToWrite = self.mainMemory[ self.frameTable[pageNumber][0] ]#La dirección física es tanto de la memporia principal como de secundaria
			csvWriter = csv.writer(pageToWrite)	
		else: # Si la página está en memoria secundaria.
			mainMemIndex = self.olderPageIndex % MAIN_MEMORY_PAGE_COUNT
			pageName = self.mainMemory[mainMemIndex].name
			mainMemoryPageNumber = int( os.path.basename(pageName).rsplit('.',1)[0] ) 
			self.doSwap( mainMemoryPageNumber, pageNumber, mainMemIndex, self.frameTable[pageNumber][0] )
			pageName = self.mainMemory[mainMemIndex].name
			mainMemoryPageNumber = int( os.path.basename(pageName).rsplit('.',1)[0] ) 
			pageToWrite = self.mainMemory[ self.frameTable[mainMemoryPageNumber][0] ]
			csvWriter = csv.writer(pageToWrite)
			self.olderPageIndex += 1
		try:
			csvWriter.writerow(packageInfo)
		except csv.Error as e:
			print("Failed to write")
		pageToWrite.flush() 
			
	def doSwap(self, pageMainMem, pageSecondMem, mainMemIndex, secondMemIndex):
		temp = self.mainMemory[mainMemIndex]
		self.mainMemory[mainMemIndex] = self.secondaryMemory[secondMemIndex]
		self.secondaryMemory[secondMemIndex] = temp
		self.updateFrameTable(pageMainMem, secondMemIndex, SECONDARY_MEMORY)
		self.updateFrameTable(pageSecondMem, mainMemIndex, MAIN_MEMORY)
	
		
	def sendPageToInterface(self, pageNumber): # Enviar página de memoria principal a interfaz
		dataBuffer = []
		if self.frameTable[pageNumber][1] == 0:  #Se comprueba si está en la memoria principal
			pageName = self.mainMemory[ self.frameTable[pageNumber][0] ].name #name es el nombre del archivo de donde está la página
			page = int( os.path.basename(pageName).rsplit('.',1)[0] )
			self.mainMemory[ self.frameTable[pageNumber][0] ].seek(0)
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
