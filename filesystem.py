"""import os
import time
import sys
import struct
import random

diskSize = 4000
fileName = "newfile"

def writeMetaTable(pageTable, f): # Falta meterle offset 
    counter = 0
    f.seek(0)
    for i in pageTable:
        for j in i:
            f.write(struct.pack("I", j))
            counter+=1
    return counter

def writePages(offset, dateCreated,dateAccessed, data, f):
    # dateCreated, dateAccessed, Data
    f.seek(offset)
    data2 = [dateCreated,dateAccessed]
    f.write(struct.pack("I"*2, *data2))
    #f.write(struct.pack("I", dateCreated))
    #f.write(struct.pack("I", dateAccessed))
    for i in data:
        f.write(struct.pack("I", i))


def createBinaryFile(name, size):
    f = open(name, "wb")
    f.seek(size-1)
    f.write(b"\0")
    f.close()

def readBinaryFile(name, size):
    with open(name, mode='rb') as f: # b is important -> binary
        #f.seek(24)
        fileContent = f.read()
        #ints = struct.unpack('i'*((size-24)//4), fileContent[:size-24])
        ints = struct.unpack('i'*(size//4), fileContent[:size])
        print(ints)
        #print(sys.getsizeof(ints)//4) # cantidad de ints
"""
"""
ID-NM				
                GUARDAR				
OPERACION	PAGINA_ID	TAMAÑO_PAGINA	DATOS	
1 BYTE	    1 BYTE	    4 BYTES	        TAMAÑO_PAGINA BYTES	
				
                PEDIR				
OPERACION	PAGINA_ID			
1 BYTE	    1 BYTE			
				
                OK				
OPERACION				
1 BYTE				
"""


"""def getOffsetPages()

offsetMetaData = 
offsetPages = (diskSize) - (pagesInDisk * (pageSize + dateSize * 2))
def savePage(pageID, pageSize, data)"""

"""
def getContent(index, contentSize, f):
    f.seek(index)
    fileContent = f.read()
    content = struct.unpack('i' * (contentSize//4), fileContent[:contentSize])
    return content


def getPageData(pageID, f):
    index = 0
    f.seek(index)
    currentPageID = getContent(index, 4, f)
    while currentPageID != pageID: 
        index += 12
        currentPageID = getContent(index, 4, f)[0]
    index += 4  # 4 de pageSize y 4 de offset
    metaData = getContent(index, 8, f)
    pageSize = metaData[0]
    pageOffset = metaData[1]+8
    #print(pageOffset)
    #print(pageOffset, pageSize)
    data = getContent(pageOffset, pageSize, f)
    print(data)
    return data


# Cada fila de metadatos (cada pag) son 3 ints - El id puede ser menor, pero primero como int
# Se inserta al inicio las filaPagA,filaPagB,...etc
# Orden Fin - Inicio DatosN,DatosN-1,...DatosA. Cada Datos tiene Fecha de Creacion + Fecha Ultimo acceso
pageSize = 20
metaTable = []
offset = diskSize
dateSize = (int)(sys.getsizeof(time.time())) // 4
#dateSize = ((int)(time.time())).__sizeof__()
#print(dateSize)
pagesInDisk = 0
for i in range(random.randint(3,3)):
    pagesInDisk += 1 # Para efectos de esta simulacion
    pageBase = (diskSize) - (pagesInDisk * (pageSize + 8)) # Probablemente se ocupe un segundo pageSize pagesInDiskType1 * pageSize1 + pagesInDiskType2 * pageSize2
    row = [i, pageSize, pageBase]
    metaTable.append(row)
    print(metaTable[i])

createBinaryFile(fileName, diskSize)
dateCreated = (int)(time.time())
dateAccessed = (int)(time.time())
with open(fileName, "r+b") as f:
    writeMetaTable(metaTable, f)
    data = [40,50,60,70,80]
    counter = 0
    for x in data:
        counter += 4
    #print("Contador: ", counter)
    writePages(metaTable[0][2], dateCreated, dateAccessed, data, f)
    writePages(metaTable[1][2], dateCreated, dateAccessed, data, f)
    writePages(metaTable[2][2], dateCreated, dateAccessed, data, f)
    getPageData(2,f)
readBinaryFile(fileName, diskSize)

def run():
    packetOpCode = 0

"""

"""with open("newfile", mode='rb') as file: # b is important -> binary
    fileContent = file.read()
    ints = struct.unpack('iiii'*, fileContent[:32])
    print(ints)
    #print(struct.unpack("i" * ((len(fileContent) -24) // 4), fileContent[20:-4])"""

""" QUEMAR DATOS para la demo"""

import os
import time
import sys
import struct
import random
from datetime import datetime
from tabulate import tabulate

class FileSystem:
    
    def __init__(self, fileName, diskSize):
        self.diskSize = diskSize
        self.fileName = fileName
        self.createBinaryFile()
        self.file = open(self.fileName, 'r+b')
        self.file.seek(0)
        self.file.write(struct.pack("I", diskSize - 12))
        self.file.write(struct.pack("I", 12))
        self.file.write(struct.pack("I", diskSize))

    def getSpaceAvailable(self):
        return self.getContent(0,4)[0]
    
    def setSpaceAvailable(self, spaceAvailable):
        self.file.seek(0)
        self.file.write(struct.pack("I", spaceAvailable))

    def getMetaDataOffset(self):
        return self.getContent(4, 4)[0]

    def setMetaDataOffset(self):
        offset = self.getMetaDataOffset()
        self.file.seek(4)
        self.file.write(struct.pack("I", offset + 12))
    
    def getPagesOffset(self):
        return self.getContent(8,4)[0]
    
    def setPagesOffset(self, pageSize):
        offset = self.getPagesOffset()
        self.file.seek(8)
        self.file.write(struct.pack("I", (offset - pageSize - 8)))

    # Escribe meta datos de inicio a fin, hasta chocar con los datos de las paginas
    def writeMetaData(self, metaData):
        self.file.seek(self.getMetaDataOffset())
        self.file.write(struct.pack("I"*len(metaData), *metaData))
        self.setMetaDataOffset()
        self.setSpaceAvailable(self.getSpaceAvailable() - 8)

    def writePageData(self, pageSize, data):
        self.file.seek(self.getPagesOffset())
        #times = [(int)(time.time()), (int)(time.time())]
        self.file.write(struct.pack("I"*2, (int)(time.time()), (int)(time.time())))
        self.file.write(struct.pack("I"*len(data), *data))
        self.setSpaceAvailable(self.getSpaceAvailable() - pageSize - 8)

    def createBinaryFile(self):
        if os.path.exists(self.fileName):
            os.remove(self.fileName)
        file = open(self.fileName, "x+b")
        file.seek(self.diskSize-1)
        file.write(b"\0")
        file.close()
        #return file

    def readBinaryFile(self):
        self.file.close()
        with open(self.fileName, mode='r+b') as file: # b is important -> binary
            fileContent = (file).read()
            content = struct.unpack('i'*(self.diskSize//4), fileContent[:self.diskSize])
            print(content)
        self.file = open(self.fileName, "r+b")

    def getContent(self, index, contentSize): # Index: desde 0 hasta diskSize - 1  y contentSize en bytes
        self.file.seek(index)
        fileContent = self.file.read()
        content = struct.unpack('i' * (contentSize//4), fileContent[:contentSize])
        return content

    def savePage(self, pageId, pageSize, data):
        if self.getSpaceAvailable() - pageSize - 12 - 8 >= 0: # 12 de MetaDatos y 8 de ambas fechas
            self.setPagesOffset(pageSize)
            self.writeMetaData((pageId, pageSize, self.getPagesOffset()))
            self.writePageData(pageSize, data)
        else:
            print("Escritura fallida. No hay suficiente espacio disponible.\nEspacio disponible:", self.getSpaceAvailable(),"bytes.")

    def getPageData(self, pageID):
        index = 12   # Al inicio esta diskAvailable, metaDataOffset y pageOffset. 12 es para llegar a los metadatos 
        self.file.seek(index)
        currentPageID = self.getContent(index, 4)[0]
        while currentPageID != pageID and index < self.getMetaDataOffset(): 
            index += 12
            currentPageID = self.getContent(index, 4)[0]
        if currentPageID == pageID:
            index += 4 # Movimiento para agarrar solo pageSize y la direccion de la pagina actual 
            metaData = self.getContent(index, 8)
            data = self.getContent(metaData[1]+8,metaData[0])
            print(data)
            return data
        else: 
            print("La pagina con id", pageID,"no se encuentra en este nodo.")
            return -1
    
    def getPageDates(self, index):
        self.file.seek(index)
        return self.getContent(index, 8)
    
    def listFiles(self):
        print("Si quiere ver informacion sobre las paginas actuales ubicadas en este nodo, digite ls")
        request = input()
        if request == "ls":
            information = [] # ID, dateC, dateAcc, pageSize, address
            for x in range(12, self.getMetaDataOffset(), 12):
                pageInformation = []
                metaData = self.getContent(x, 12)
                dates = self.getPageDates(metaData[2])
                pageInformation.append(str(metaData[0]))
                pageInformation.append(datetime.strftime(datetime.utcfromtimestamp(dates[0]),"%b %d %H:%M:%S"))
                pageInformation.append(datetime.strftime(datetime.utcfromtimestamp(dates[1]),"%b %d %H:%M:%S"))
                pageInformation.append(str(metaData[1]))
                pageInformation.append(str(metaData[2]))
                information.append(pageInformation)
            print(tabulate([*information], headers=['Page ID', 'Date Created', 'Date Accessed', "Page Size", "Adddress"]))


    """def run(self):
        self.diskSize = 4000
        self.fileName = "newfile"
        self.createBinaryFile()"""
#print("Inserte el nombre del archivo")
#name = input()
#print("Inserte el tamano del archivo")
#size = int(input())
name = "newfile"
size = 240000
fs = FileSystem(name,size)
fs.savePage(1, 20, (4,5,6,7,8))
fs.savePage(2, 20, (4,5,6,7,8))
fs.savePage(3, 20, (4,5,6,7,8))
fs.savePage(4, 28, (4,5,6,7,8,9,10))
fs.savePage(5, 20, (666,777,888,999,420))
fs.savePage(6, 20, (4,5,6,7,8))
fs.savePage(7, 24, (4,5,6,7,8,9))
#fs.getPageData(5)
#fs.getPageData(7)
#fs.getPageData(9)
fs.listFiles()
#fs.readBinaryFile()