import struct
import queue
import threading
import time
from time import sleep
import socket
import sys

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

#
IP_BROACAST = "192.168.1.255"

#
PORT_BROADCAST = 5000

#
IP = "192.168.1.32"

#
PORT = 3114


class DistributedMemoryProtocol:
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
    socket = None
    waitSendId = None
    kappa = None


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
        self.kappa = threading.Semaphore(1)
        self.socket = None
        self.waitSendId = False

    def run(self):
        sendRequest = threading.Thread(target= self.sendPage)
        sendRequest.start()
        savePageRequest = threading.Thread(target= self.receivePage)
        savePageRequest.start()
        classifier = threading.Thread(target= self.classifyPackets)
        classifier.start()
        self.sendRegisterSignal(self.nodeCurrentMemory)

    def sendPage(self):
        while True:
            if (not self.sendToInterfaceRequest.empty()): #Espera unicamente el # de página
                print("Entre")
                packet = []
                pageToBeSended = self.sendToInterfaceRequest.get()
                self.pageInfo = [pageToBeSended]
                self.requestInfoToNode.release()
                self.infoAlreadyAvailable.acquire()
                infoSize = len(self.pageInfo)
                packetFormat = '=1s 1s'
                print("Page info:" , self.pageInfo)
                for x in range (1,infoSize):
                    packetFormat = packetFormat + ' I'
                packetStruct = struct.Struct(packetFormat)
                packet.append(bytearray([SEND]))
                packet.append(bytearray([pageToBeSended]))
                print("Paquete: ", packet)
                for x in range (1,infoSize):
                    packet.append(self.pageInfo[x])
                print(packet)
                packedData = packetStruct.pack(*( tuple(packet) ))
                #Enviar paquete a ID
                self.socket.send(packedData)
                self.socket.close()
                self.kappa.release()
                self.waitSendId = False

    def receivePage(self):
        while True:
            if(not self.receivePageFromInterface.empty()):
                print("Recibir")
                self.pageInfo = [] #Coloca en 0 el número de página y el resto la info
                pageReceived = self.receivePageFromInterface.get()
                print(pageReceived)
                for x in range (0,len(pageReceived)):
                    self.pageInfo.append(pageReceived[x])
                self.sendInfoToNode.release()
                self.infoSetInNode.acquire()
                packet = []
                packetStruct = struct.Struct('=1s 1s I')
                packet.append(bytearray([OK]))
                packet.append(bytearray([pageReceived[0]]))
                packet.append(self.nodeCurrentMemory)
                print("Paquete: ", packet)
                # Enviar mensaje de ok
                packetData = packetStruct.pack( * ( tuple(packet) ) )
                self.socket.send(packetData)
                self.socket.close()
                self.kappa.release()
                self.waitSendId = False


    def sendRegisterSignal(self,spaceAvailable):
        while True:
            packet = []
            packetStruct = struct.Struct('=1s I')
            packet.append(bytearray([IAMHERE]))
            packet.append(spaceAvailable)
            packetInfo = packetStruct.pack( * ( tuple(packet) ) )
            #Se envia el paquete
            server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Permitir broadcast
            server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            server.sendto(packetInfo, (IP_BROACAST, PORT_BROADCAST) )

            timeout = time.time() + 4
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
        while True:
            if(not self.waitSendId):
                self.kappa.acquire()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                s.bind( (IP, PORT) )
                s.listen(1)
                self.socket,addr = s.accept()
                packetStruct = struct.Struct('=1s')
                try:
                    data = self.socket.recv(700000)
                except socket.error:
                    print("Connection lost with ID when waiting a message")  #No tiene sentido
                if(data):
                    self.waitSendId = True
                    unpackedData = list(packetStruct.unpack(data[:1]))
                    operationCode =  struct.unpack('>H',b'\x00' + unpackedData[0] )[0]
                    if(operationCode == SAVE_PAGE):
                        packetFormat = '=1s 1s I'
                        packetStruct = struct.Struct(packetFormat)
                        unpackedData = list(packetStruct.unpack(data[:6]))
                        size = unpackedData[2]
                        for x in range(0,size//4):
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
                    elif(operationCode == REQUEST_PAGE):
                        packetStruct = struct.Struct('=1s 1s')
                        unpackedData = list(packetStruct.unpack(data[:2]))
                        page = struct.unpack('>H',b'\x00' + unpackedData[1] )[0]
                        self.sendToInterfaceRequest.put(page)
                    elif(operationCode == OK):
                        self.okFromID.put(None)
                        self.waitSendId = False
                        self.socket.close()
                        self.kappa.release()



#kappa = DistributedIMemoryProtocol()
#kappa.run()
