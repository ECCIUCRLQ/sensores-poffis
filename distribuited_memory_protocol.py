import struct
import queue
import threading
import time
import socket

## Operation codes.
SAVE_PAGE = 0
REQUEST_PAGE = 1
OK = 2
SEND = 3
ERROR = 4
IAMHERE = 5

## Queue size.
QUEUE_SIZE = 10000

## Page size
PAGE_SIZE = 691200

## Data size.
DATA_SIZE = 4

## Number of integers peer page.
DATA_COUNT = PAGE_SIZE // DATA_SIZE

class DistributedIMemoryProtocol:
    receivePageFromInterface = None
    sendToInterfaceRequest = None
    okFromID = None
    pageInfo = None
    nodeCurrentMemory = None
    requestInfoToNode = None
    infoAlreadyAvailable = None
    sendInfoToNode = None
    infoSetInNode = None
    conn = None
    

    def __init__(self):
        self.receivePageFromInterface = queue.Queue(QUEUE_SIZE)
        self.sendToInterfaceRequest = queue.Queue(QUEUE_SIZE)
        self.okFromID= queue.Queue(QUEUE_SIZE)
        self.pageInfo = []
        self.nodeCurrentMemory = 0
        self.requestInfoToNode = threading.Semaphore(0)
        self.infoAlreadyAvailable = threading.Semaphore(0)
        self.sendInfoToNode = threading.Semaphore(0)
        self.infoSetInNode = threading.Semaphore(0)
        IPID = '192.168.1.2' #Cambiar
        port = 6000
        bufferSize = 1
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((IPID,port))
        s.listen(1)
        self.conn, addr = s.accept()



    def run(self):
        sendRequest = threading.Thread(target= self.sendPage)
        sendRequest.start()
        savePageRequest = threading.Thread(target= self.receivePage) 
        savePageRequest.start()
        classifier = threading.Thread(target= self.classifyPackets)
        classifier.start()
        while True:
            kappa = 2


    def sendPage(self):
        while True:
            if (not self.sendToInterfaceRequest.empty()): #Espera unicamente el # de página
                packet = []
                pageToBeSended = self.sendToInterfaceRequest.get()
                print(pageToBeSended)
                self.pageInfo = []
                self.requestInfoToNode.release()
                self.infoAlreadyAvailable.acquire()
                infoSize = len(self.pageInfo)
                packetFormat = '1s 1s'
                for x in range (0,infoSize):
                    packetFormat = packetFormat + ' I'
                packetStruct = struct.Struct(packetFormat)
                packet.append(SEND)
                packet.append(pageToBeSended)
                for x in range (0,infoSize):
                    packet.append(self.pageInfo[x])
                packetStruct.pack( *( tuple(packet) ) )
                #Enviar paquete a ID
                
    def receivePage(self):
        while True:
            if(not self.receivePageFromInterface.empty()):
                self.pageInfo = [] #Coloca en 0 el número de página y el resto la info
                pageReceived = self.receivePageFromInterface.get()
                #print(pageReceived)
                for x in range (0,len(pageReceived)):
                    self.pageInfo.append(pageReceived[x])
                self.sendInfoToNode.release()
                self.infoSetInNode.acquire() #A este punto ya está actualizado el nodo y en self.nodeCurrentMemory se colocó el espacio que le queda al nodo
                packet = []
                packetStruct = struct.Struct('1s 1s I')
                packet.append(bytearray(OK))
                packet.append(bytearray(pageReceived[0]))
                packet.append(self.nodeCurrentMemory)
                packetStruct.pack( * ( tuple(packet) ) )

                # Enviar mensaje de ok

    def sendRegisterSignal(self,spaceAvailable):
        while True:
            packet = []
            packetStruct = struct.Struct('1s I')
            packet.append(bytearray(IAMHERE))
            packet.append(bytearray(spaceAvailable))
            packetStruct.pack( * ( tuple(packet) ) )
            #Se envia el paquete
            timeout = time.time() + 10
            registed = False
            while True:
                if(not self.okFromID.empty()):
                    registed = True
                    break
                else:
                    if time.time() > timeout:
                        break
            if registed:
                break
                    





    def classifyPackets(self):
        packetStruct = struct.Struct('1s')
        while True:
            data = conn.recv(700000)
            if(data):
                #print(data)
                bufferSize = 700000
                unpackedData = list(packetStruct.unpack(data[:1]))
                operationCode =  struct.unpack('>H',b'\x00' + unpackedData[0] )[0]
                if(operationCode == SAVE_PAGE):
                    packetFormat = '1s 1s I'
                    packetStruct = struct.Struct(packetFormat)
                    unpackedData = list(packetStruct.unpack(data[:8]))
                    size = unpackedData[2]
                    for x in range(0,size):
                        packetFormat = packetFormat + ' I'
                    packetStruct = struct.Struct(packetFormat)
                    unpackedData = list(packetStruct.unpack(data))
                    dataReceived = []
                    pageID = unpackedData[1]
                    pageID = struct.unpack('>H',b'\x00' + pageID )[0]
                    dataReceived.append(pageID)
                    for x in range (3,len(unpackedData)):
                        dataReceived.append(unpackedData[x])
                    self.receivePageFromInterface.put(dataReceived)
                    #print(unpackedData)
                elif(operationCode == REQUEST_PAGE):
                    packetStruct = struct.Struct('1s 1s')
                    unpackedData = list(packetStruct.unpack(data[:2]))
                    page = struct.unpack('>H',b'\x00' + unpackedData[1] )[0]
                    self.sendToInterfaceRequest.put(page)
                


kappa = DistributedIMemoryProtocol()
kappa.run()





