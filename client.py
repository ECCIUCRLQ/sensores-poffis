import socket
import binascii
import struct
import sys
import time
import random
import string
import threading
import queue
from ultrasonic_sensor import bat_belt
from sound_sensor import librarian_nark

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
UDP_IP = "192.168.0.11"			  # Destino
UDP_PORT = 5000				  # Destino

UDP_IP_CLIENT = "127.0.0.1"  		  # IP Cliente - espera respuesta del server
UDP_PORT_SERVER_REPLY = 5005		  # Port en el que viene la respuesta del server
sock.bind((UDP_IP_CLIENT, UDP_PORT_SERVER_REPLY)) # Bind para respuesta del server
carretaInt = struct.Struct('1s I 4s 1s I') 
bueyPack = struct.Struct('1s 4s')
timeCommLimit, timeRIDLimit = 1.0, 3
ridWanted = ''

def sendPackage(sensorId, sensorCode, data, socket): # Verificar numero del tipo de dato
	randomID = random.choice(string.ascii_letters)
	values = (randomID.encode(), int(time.time()), bytearray([6,0,0,sensorId]), chr(sensorCode).encode(), data)
	print(values)
	packedData = carretaInt.pack(*values) 
	unpackedData = carretaInt.unpack(packedData)
	print(unpackedData)
	socket.sendto(packedData, (UDP_IP, UDP_PORT))
	return packedData, randomID, True		

# Si no hay mensajes que neviar, enviar keepalive
def main():
	##########################Sensors init##############################
	#Ultrasonic_sensor
	path_length=50
	frecuency=1
	batarang = bat_belt()
	batarang.throw_batarang(path_length,frecuency)
	#Sound sensor
	rat = librarian_nark()
	
	"""
	Read sound sensor
		value = rat.tell_on_someone(gain)
		%: Sensibility of the sensor
	Read ulrasonic sensor
		value = batarang.catch_batarang()	
		
	"""
	####################################################################
	
	ridReceived = ''  
	timeCommStart, timeRIDStart = time.time(), time.time()
	lastSent, ridWanted, waitingReply = sendPackage(1, 9, random.randint(0,4294967295), sock) # tipo y data segun el get del sensor
	while True:
		if waitingReply == True: 
			try: 
				sock.settimeout(timeRIDLimit)
				data, addr = sock.recvfrom(bueyPack.size)  
				sock.settimeout(0)
				unpackedData = bueyPack.unpack(data)
				ridReceived = (unpackedData[0]).decode()
				print("Recibi buey:", unpackedData)
				waitingReply = False 
			except: # Si sucede un timeout.
				print("Random ID was not received. Resending last packet.") 
				#print(time.time() - timeRIDStart)
				sock.sendto(lastSent, (UDP_IP, UDP_PORT)) # Ya esta empacado, no ocupa casos
				timeCommStart, timeRIDStart = time.time(), time.time()
		else:	
			if ridReceived == ridWanted:    # Un paquete fue recibido, se verifica si es el deseado mediante el RID. 
				print("Packet sent.")
				#print(time.time() - timeCommStart)
				lastSent, ridWanted, waitingReply = sendPackage(1, 9, random.randint(0,4294967295), sock) # tipo y data segun el get del sensor
				timeCommStart, timeRIDStart = time.time(), time.time()
			else:  # Recibe un ACK duplicado.
				print("Random ID did not match. Resending last packet.")
				sock.sendto(lastSent, (UDP_IP, UDP_PORT)) # Ya esta empacado, no ocupa casos.
				timeCommStart, timeRIDStart = time.time(), time.time()
				waitingReply = True 
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
