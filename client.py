import socket
import binascii
import struct
import sys
import time
import random
import string

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
UDP_IP = "192.168.0.11" #"10.1.138.34"
UDP_PORT = 5000
sock2.bind((UDP_IP, 5005))
packer1 = struct.Struct('1s f 4s 1s 7s') #  Hacer casos de los datos segun tipo 
packer2 = struct.Struct('1s f 4s 1s f') #  Hacer casos de los datos segun tipo 
#bueyPack = struct.Struct('1s 4s')
timeCommLimit, timeRIDLimit = 1.0, 3.0
ridWanted = ''

def sendPackage(sensorType, data, socket): 
	randomID = random.choice(string.ascii_letters)
	values = (randomID.encode(), float(time.time()), bytearray([0,1,2,3]), sensorType.encode(), data.encode())
	print(values)
	if sys.getsizeof(data)//8 == 7:
		packed_data = packer1.pack(*values)
		#print(sys.getsizeof(packed_data)//8) # Cantidad de bytes 
	else: 
		packed_data = packer2.pack(*values)
		#print(sys.getsizeof(packed_data)//8) # Cantidad de bytes 
	#print('{!r}', format(binascii.hexlify(packed_data))) #hexa #print(values) 
	#print(packer2.unpack(packed_data))
	socket.sendto(packed_data, (UDP_IP, UDP_PORT))
	return packed_data, randomID, True

def main():
	ridReceived = ''  
	timeCommStart, timeRIDStart = time.time(), time.time()
	lastSent, ridWanted, waitingReply = sendPackage(hex(0), "Carreta", sock) # tipo y data viene del sensor
	while True:
		if waitingReply == True:
			data, addr = sock2.recvfrom(20)  # Para recibir Buey del receiver
			unpackedData = packer1.unpack(data)
			ridReceived = (unpackedData)[0].decode()
			if ridReceived == ridWanted:
				print("Recibi buey:", unpackedData)
				waitingReply = False #, serverReplied = False, True
		else:
			if waitingReply and time.time() - timeRIDStart >= timeRIDLimit: #timeout, no recibio RID
				print("Random ID was not received. Resending last packet.") 
				print(time.time() - timeRIDStart)
				sock.sendto(lastSent, (UDP_IP, UDP_PORT)) # Ya esta empacado, no ocupa casos
				timeCommStart, timeRIDStart = time.time(), time.time()
				serverReplied = False #waitingReply, serverReplied = True, False
			elif not waitingReply and time.time() - timeCommStart >= timeCommLimit: # Recibio RID, quitar segunda condicion para cuando ya este implementado con sensor y server
				if ridReceived == ridWanted:    # Hay posibilidad de RID duplicados en Sender? Si no es el esperado reenvia y el control es en el receiver
					print("Packet sent.")
					print(time.time() - timeCommStart)
					lastSent, ridWanted, waitingReply = sendPackage(hex(0) , "Carreta", sock) # tipo y data viene del sensor
					timeCommStart, timeRIDStart = time.time(), time.time()
				elif ridWanted != ridReceived: # Resend
					print("Random ID did not match. Resending last packet.") #print(time.time() - timeACKStart)
					sock.sendto(lastSent, (UDP_IP, UDP_PORT)) # ya esta empacado, no ocupa casos
					timeCommStart, timeRIDStart = time.time(), time.time()
					waitingReply = True #waitingReply, serverReplied = True, False
main()

"""Protocolo del cliente al servidor	
Random ID	1 byte
Date	4 bytes
SensorID	4 bytes
Tipo de sensor	1 byte
Datos	
	
Protocolo servidor-cliente	
Random ID	1 byte
Sensor ID	4 bytes"""
