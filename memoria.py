import csv
def createNewPage(pageNumber): #Crea nueva página en memoria principal
	f = open(str(pageNumber)+".csv", "x")
	
def writePage(pageNumber,date,data): #Escribir en memoria principal
	# Abre el archivo,
	f = open(str(pageNumber)+".csv", "a")
	vctr=[date,data]
	csvWriter = csv.writer(f)
	csvWriter.writerow(vctr)
	
def sendInfoInDisk(sensorID): #lee y manda a interfaz lo de ese sensor en memoria secundaria
	f = open(str(sensorID)+".csv", "r")
	csvReader = csv.reader(f,delimiter = ',')
	dataBuffer=[]
	for row in csvReader:
		dataBuffer.append(row)
	return dataBuffer
	
def sendPageToInterface(pageNumber,dataBuffer): # Enviar página de memoria principal a interfaz
	f = open(str(pageNumber)+".csv", "r")
	csvReader = csv.reader(f,delimiter = ',')
	for row in csvReader:
		dataBuffer.append(row)
	return dataBuffer
	
#def write_in_disk(sensorID,page_number): # envia a memoria secundaria
	
#for x in range(6):
#	write_page(x,1,1)
	
	
