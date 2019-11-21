import threading
import time
from memory import MemoryManager

### Operation codes
SAVE_PAGE = 0
REQUEST_PAGE = 1
OK = 2
SEND = 3
ERROR = 4
I_AM_HERE = 5

I_WANT_TO_BE_ACTIVE = 0
I_AM_ACTIVE = 1
KEEP_ALIVE = 2

###Protocols
ML_ID_ML = 0
ID_NM_ID = 1
ID_ID = 2



class distributedInterface:

	### ML-ID packets.
	savePages = '1s 1s I '
	askForPages = '1s 1s'

	### ID-ML
	ok = '1s 1s'
	sendPage = '1s 1s'

	### ID-ID
	iWantToBeChampion = '1s 6s 1s'
	updateTables = '1s 1s 1s'
	keepAlive = '1s 1s 1s'

	## NM-ID
	newMemoryNode = '1s I'
	availableSpace = '1s 1s I'
	
	## Operation code unpack
	operationCode = '1s'

	def __init__(self):
		
		
	def receiveRequestToSave():
		
		
	def receiveRequestToSend():
	
	
	def receivePackets(packet,protocolType):
		operationCodeStruct = struct.Struct(operationCode)
		operationCodeValue = operationCodeStruct.unpack(packet)[0].decode()
		if(operationCodeValue 0):
			if(protocolType = 0):
				### SAVE PAGE ML TO ID
			if(protoclType) 
		
	
	
