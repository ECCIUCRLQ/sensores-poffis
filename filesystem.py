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

    def updateDateAccessed(self, offset):
        self.file.seek(offset)
        self.file.write(struct.pack("I", (int)(time.time())))


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
            self.updateDateAccessed(metaData[1]+4)
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
        # Un thread para guardar y 2 para lecturas
        self.savePage(pageId, pageSize, data)
        self.getPageData( pageID)"""

print("Inserte el nombre del archivo")
name = input()
print("Inserte el tamano del archivo")
size = int(input())
#name = "newfile"
#size = 240000
fs = FileSystem(name,size)
fs.savePage(1, 20, (4,5,6,7,8))
fs.savePage(2, 20, (4,5,6,7,8))
fs.savePage(3, 20, (4,5,6,7,8))
fs.savePage(4, 28, (4,5,6,7,8,9,10))
fs.savePage(5, 20, (666,777,888,999,420))
fs.savePage(6, 20, (4,5,6,7,8))
fs.savePage(7, 24, (4,5,6,7,8,9))
x = time.time()
while time.time() - x < 5:  # Para tener diferente fecha de acceso y creacion
    a = 8
fs.getPageData(5)
#fs.getPageData(5)
#fs.getPageData(7)
#fs.getPageData(9)
fs.listFiles()
#fs.readBinaryFile()