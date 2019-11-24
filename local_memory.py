import csv
import numpy as matrix
import os
from local_memory_protocol import LocalMemoryProtocol 
 
#Two of the four pages of main memory are reserved to write ops 
MAIN_MEM_PAG_WRT = 2
#Two of the four pages of main memory are reserved to read ops
MAIN_MEM_PAG_RED = 2
#Arbitrary number, represent the max page capacity the system can handle 
SYS_PAG_CAP=100
#3600s * 24h * 2ints-of-data + 1 for identifier
#PAG_SZE=172801
PAG_SZE=11
#Location flag | Capacity Flag
#Identifier is given by the position in the array 
INFO_PER_PAGE = 2

#Flag values
MAIN_MEMORY = 0
SECONDARY_MEMORY = 1
NOT_FULL = 0
FULL = 1


class MemoryManager:
	
	def __init__(self):
		self.frameTable = matrix.zeros( shape = (SYS_PAG_CAP, INFO_PER_PAGE), dtype = int )  		 
		self.mainMemory = matrix.zeros( shape = (4, PAG_SZE), dtype = int )
		self.nextId = 0
		self.olderPageBrought = 0
		self.messenger = LocalMemoryProtocol()
		self.messenger.run()
	
	def updateFrameTable(self, pageNumber, location, cap_stat):
		self.frameTable[pageNumber][0] = location
		self.frameTable[pageNumber][1] = cap_stat
	
	def createNewPage(self): 
		if self.nextId < SYS_PAG_CAP:
			#This is useful when the MM is not totally assigned 
			if self.nextId < MAIN_MEM_PAG_WRT: 
				self.mainMemory[self.nextId][0]=self.nextId
				self.updateFrameTable(self.nextId, MAIN_MEMORY, NOT_FULL)
			else:
				pageToReplace = self.search_full_pag()
				self.sendToSecondaryMemory(pageToReplace) #Se envía a memoria secundaria
				self.updateFrameTable(self.mainMemory[pageToReplace][0], SECONDARY_MEMORY, FULL)
				self.mainMemory[pageToReplace][0] = self.nextId
				self.updateFrameTable(self.nextId, MAIN_MEMORY, NOT_FULL)
			
			self.nextId += 1
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


	def sendToSecondaryMemory(self, pageToReplace):
		#!self.messenger.pagesToSave.put(self.mainMemory[pageToReplace])
		#!self.messenger.okeyAlreadyRead.acquire()
		self.updateFrameTable(pageToReplace, SECONDARY_MEMORY, FULL)

	#Since straight targeting is no loger used this method is needed to find the position of a page in MM 
	def get_MM_index(self, pageNumber):
		for memIndx in range(MAIN_MEM_PAG_WRT):
			if self.mainMemory[memIndx][0] == pageNumber:
				return memIndx

	#Since no page can be sent to secondary memory in a state different from full, page to be written must be always in main memory	
	def writePage(self, pageNumber, date, data, offset, cap_stat):
		offset += 1
		if self.frameTable[pageNumber][0] == MAIN_MEMORY:
			position = self.get_MM_index(pageNumber)
			self.mainMemory[position][offset] = date
			self.mainMemory[position][offset+1]=data
			self.updateFrameTable(pageNumber, MAIN_MEMORY, cap_stat)
		
		else: 
			print("Fail to write")

	def requestPage(self, pageNumber):
		if self.frameTable[pageNumber][0] == MAIN_MEMORY:
			position = self.get_MM_index(pageNumber)
			dataBuffer = self.mainMemory[position]
		else:
			self.messenger.requestedPages.put(pageNumber)
			while True:
				#Watch out for race conditions  
				if not self.messenger.requestedPages.empty():
					break
			position = self.olderPageBrought % 2 + 2
			self.updateFrameTable(self.mainMemory[position][0], SECONDARY_MEMORY, FULL)
			self.mainMemory[position] = self.messenger.requestedPages.get()
			self.updateFrameTable(self.mainMemory[position][0], MAIN_MEMORY, FULL)
			dataBuffer = self.mainMemory[position]
			self.olderPageBrought += 1
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
