import binascii
import socket
import struct
import sys

UDP_IP = "192.168.0.11"
UDP_PORT = 5000

UDP_IP_CLIENT = "127.0.0.1"  		  # IP Cliente - IP para responder al cliente
UDP_PORT_SERVER_REPLY = 5005		  # Port para repsonder


carretaInt = struct.Struct('1s I 4s 1s I') 
bueyPack = struct.Struct('1s 4s')

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP				 
sock.bind((UDP_IP, UDP_PORT))

while True:
	data, addr = sock.recvfrom(carretaInt.size)
	#print ('received message: {!r}',  format(binascii.hexlify(data)))
	unpackedData = carretaInt.unpack(data)
	#print ('unpacked: ', unpackedData)

	newPackage = (unpackedData[0], unpackedData[2])
	packedData = bueyPack.pack(*newPackage)
	print(newPackage)
	sock.sendto(packedData, (UDP_IP_CLIENT, UDP_PORT_SERVER_REPLY))

"""Protocolo del cliente al servidor	
Random ID	1 byte
Date	4 bytes
SensorID	4 bytes
Tipo de sensor	1 byte
Datos	
	
Protocolo servidor-cliente	
Random ID	1 byte
Sensor ID	4 bytes"""
