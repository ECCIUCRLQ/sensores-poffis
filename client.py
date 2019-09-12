import socket
import binascii
import struct
import sys
import time
import random
import string

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
UDP_IP = "192.168.0.11" #"10.1.138.34"
UDP_PORT = 5000
packer1 = struct.Struct('1s f 4s 1s 1s') #  Hacer casos de los datos segun tipo 
packer2 = struct.Struct('1s f 4s 1s f') #  Hacer casos de los datos segun tipo 
timeCommLimit, timeACKLimit = 1.0, 3.0

def sendPackage(sensorType, data, socket, ackWanted): 
	values = ((random.choice(string.ascii_letters)).encode(), float(time.time()), 
			bytearray([0,1,2,3]), sensorType.encode(), data)
	print(values)
	bytesSize = sys.getsizeof(values)//8
	if sys.getsizeof(data)//8 == 1:
		packed_data = packer1.pack(*values)
		#print(sys.getsizeof(packed_data)//8) # Cantidad de bytes 
	else: 
		packed_data = packer2.pack(*values)
		#print(sys.getsizeof(packed_data)//8) # Cantidad de bytes 
	#print('{!r}', format(binascii.hexlify(packed_data))) #hexa #print(values) 
	#print(packer2.unpack(packed_data))
	#print(sys.getsizeof(packer2.unpack(packed_data))//8)
	socket.sendto(packed_data, (UDP_IP, UDP_PORT))
	return packed_data, ackWanted + bytesSize 

def sendACK(ackWanted):
	sock.sendto(ackWanted.encode(), (UDP_IP, UDP_PORT))

def main():
	ackWanted, ackReceived = 0, -1
	timeCommStart, timeACKStart = time.time(), time.time()
	lastSent, ackWanted = sendPackage(hex(0) ,666.666, sock, ackWanted) # tipo y data viene del sensor
	sendACK(str(ackWanted))
	while True:
		"""try:
			data, addr = sock2.recvfrom(11)  # Para recibir ACK del receiver
			ackReceived = 1
		except: 
			ackReceived = 0"""
		print(ackWanted)
		ackReceived = int(input("ACK para pruebas: \n")) 
		if ackReceived == -1 and time.time() - timeACKStart >= timeACKLimit: #timeout, no recibio ACK
			print("ACK was not received. Resending last packet.") 
			print(time.time() - timeACKStart)
			sock.sendto(lastSent, (UDP_IP, UDP_PORT)) # Ya esta empacado, no ocupa casos
			timeCommStart, timeACKStart = time.time(), time.time()
			sendACK(str(ackWanted))
		elif ackReceived > -1 and time.time() - timeCommStart >= timeCommLimit: # Recibio ACK, quitar segunda condicion para cuando ya este implementado con sensor y server
			if ackReceived == ackWanted and time.time() - timeCommStart >= timeCommLimit:    # Hay posibilidad de ACK duplicados en Sender? Si no es el esperado reenvia y el control es en el receiver
				print("Packet sent.")
				print(time.time() - timeCommStart)
				lastSent, ackWanted = sendPackage(hex(0) , 777.777, sock, ackWanted) # tipo y data viene del sensor
				timeCommStart, timeACKStart = time.time(), time.time()
			elif ackWanted != ackReceived: # Resend
				print("ACK did not match. Resending last packet.") #print(time.time() - timeACKStart)
				sock.sendto(lastSent, (UDP_IP, UDP_PORT)) # ya esta empacado, no ocupa casos
				timeCommStart, timeACKStart = time.time(), time.time()			
				sendACK(str(ackWanted))
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