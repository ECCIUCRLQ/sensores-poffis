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
		self.frameTable = matrix.zeros( shape = (MAX_PAGE_COUNT, INFO_PER_PAGE), dtype = int )   		
		self.mainMemory = []
		self.secondaryMemory = [] 
		self.lastPageCreated = -1
		self.olderPageIndex = 0 
	
	def updateFrameTable(self, pageNumber, physicalAddress, secondaryMemory):
		self.frameTable[pageNumber][0] = physicalAddress
		self.frameTable[pageNumber][1] = secondaryMemory
	
	def createNewPage(self): 
		print("Older: ", self.olderPageIndex)
		if self.lastPageCreated < MAX_PAGE_COUNT: 
			self.lastPageCreated += 1 
			newPage = open( str(self.lastPageCreated) + ".csv", "a", encoding='utf-8')
			
			if self.olderPageIndex < MAIN_MEMORY_PAGE_COUNT:
				self.mainMemory.append(newPage)
				
			else:
				pageToReplace = self.olderPageIndex % MAIN_MEMORY_PAGE_COUNT
				self.sentToSecondaryMemory(pageToReplace)
				self.mainMemory[pageToReplace] = newPage

			self.updateFrameTable(self.lastPageCreated, self.olderPageIndex % MAIN_MEMORY_PAGE_COUNT  , MAIN_MEMORY)
			
				
			self.olderPageIndex += 1
			return self.lastPageCreated
		else: 
			return -1
			
	def sentToSecondaryMemory(self, pageToReplace):
		self.secondaryMemory.append( self.mainMemory[pageToReplace] )
		self.updateFrameTable(pageToReplace, len(self.secondaryMemory) - 1, SECONDARY_MEMORY)
		
	def writePage(self, pageNumber, date, data, offset): 
		packageInfo = [date,data]
		print(self.frameTable)
		#print("Page Number: ", pageNumber, "Date: ", date," and Data: ", data)
		if self.frameTable[pageNumber][1] == 0: # Si la página está en memoria principal.
			#print("Main Memory")
			print("Page Number: ", pageNumber)
			pageToWrite = self.mainMemory[ self.frameTable[pageNumber][0] ]
			#print(os.path.basename(pageToWrite.name))
			csvWriter = csv.writer(pageToWrite)	
		else: # Si la página está en memoria secundaria.
			#print("Not main memory")
			mainMemIndex = self.olderPageIndex % MAIN_MEMORY_PAGE_COUNT
			pageName = self.mainMemory[mainMemIndex].name
			mainMemoryPageNumber = int( os.path.basename(pageName).rsplit('.',1)[0] ) 
			self.doSwap( mainMemoryPageNumber, pageNumber, mainMemIndex, self.frameTable[pageNumber][0] )
			pageName = self.mainMemory[mainMemIndex].name
			mainMemoryPageNumber = int( os.path.basename(pageName).rsplit('.',1)[0] ) 
			pageToWrite = self.mainMemory[ self.frameTable[mainMemoryPageNumber][0] ]
			csvWriter = csv.writer(pageToWrite)
			self.olderPageIndex += 1
		#print("Package information: ", packageInfo)
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
		if self.frameTable[pageNumber][1] == 0:
			pageName = self.mainMemory[ self.frameTable[pageNumber][0] ].name 
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
