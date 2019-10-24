# coding=utf-8
import binascii
import random
import socket
import string
import struct
import sys
import threading
import time
import queue
from ultrasonic_sensor import MovementSensor
from sound_sensor import SoundSensor
from datetime import datetime

# Creacion del socket, definicion de IP y puerto del servidor.
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
UDP_IP = "127.0.0.1"			 
UDP_PORT = 5015	 

# SensorID = TEAM_ID + MOVEMENT_SENSOR || TEAM_ID + SOUND_SENSOR
TEAM_ID = 6
MOVEMENT_SENSOR = 9
SOUND_SENSOR = 7

# Type = MOVEMENT_DATA_TYPE || SOUND_DATA_TYPE || KEEP_ALIVE
MOVEMENT_DATA_TYPE = 2
SOUND_DATA_TYPE = 2
KEEP_ALIVE_TYPE = 0

# Creacion de un queue donde se guardan los paquetes a enviar.
QUEUE_SIZE = 10000
packetsQueue = queue.Queue(QUEUE_SIZE)

# Formato del paquete a enviar.
carretaPackage = struct.Struct('1s I 4s 1s I') 

# Formato del paquete a recibir.
bueyPackage = struct.Struct('1s 4s')

# Frecuencia de envío de paquetes y timeout (en segundos).
sendFrequency, timeOut = 0.5, 5.0

# Mutex.
lock = threading.Lock()

# last Random ID
lastRID = 'a'

def pushPacketToQueue(movementSensor, soundSensor):
	global lastRID 
	while True:
		time.sleep(sendFrequency-0.2)
		lock.acquire()
		packetMovement, lastRID = createPackage(MOVEMENT_SENSOR, lastRID, movementSensor)
		packetsQueue.put(packetMovement)
		time.sleep(sendFrequency-0.2)
		packetSound, lastRID = createPackage(SOUND_SENSOR, lastRID, soundSensor)
		packetsQueue.put(packetSound)
		lock.release()
	

def createPackage(sensorType, lastRID, sensorInstance = None):
	randomID = random.choice(string.ascii_letters).encode() 
	while lastRID == randomID:
		randomID = random.choice(string.ascii_letters).encode() 
	if sensorType == MOVEMENT_SENSOR :  # Se crea un paquete con un dato del sensor de movimiento.
		values = ( randomID, int(time.time()), bytearray([TEAM_ID, 0, 0, MOVEMENT_SENSOR]), chr(MOVEMENT_DATA_TYPE).encode(), MovementSensor.getMovementData(MovementSensor) )
	elif sensorType == SOUND_SENSOR : # Se crea un paquete con un dato del sensor de sonido.
		values = ( randomID, int(time.time()), bytearray([TEAM_ID, 0, 0, SOUND_SENSOR]), chr(SOUND_DATA_TYPE).encode(),  SoundSensor.getSoundData(SoundSensor) )
		#values = (randomID, int(time.time()), bytearray([TEAM_ID, 0, 0, ]))
	else:								# Se crea un paquete de KEEP ALIVE. 
		values = ( randomID, int(time.time()), bytearray([TEAM_ID, 0, 0, 0]), chr(KEEP_ALIVE_TYPE).encode(), 0)
	lastRID = randomID
	return carretaPackage.pack(*values), lastRID
		
def sendPackage():	
	global lastRID
	if not packetsQueue.empty() : # Si hay un paquete disponible en la cola lo envía.
		lock.acquire()
		packet = packetsQueue.get()
		lock.release()
	else: # Si no envía un paquete de tipo KEEP ALIVE, para indicar que el cliente sigue vivo pero no hay paquetes por enviar.
		packet, lastRID = createPackage(KEEP_ALIVE_TYPE, lastRID)	
	sock.sendto(packet, (UDP_IP, UDP_PORT))
	print(packet)
	return packet, True, lastRID

def main():
	movementSensor = MovementSensor()
	movementSensor.throw_batarang()
	soundSensor = SoundSensor()
	# Crea un thread que ejecuta la subrutina pushPacketToQueue cada segundo.
	threading.Thread(target=pushPacketToQueue, args = (movementSensor, soundSensor) ).start()
	global lastRID
	timeCommStart = time.time()
	lastSent, waitingReply, lastRID =  sendPackage()
	randomIdWanted = carretaPackage.unpack(lastSent)[0].decode()
	while True:		
		if waitingReply == True: 
			try: 
				sock.settimeout(timeOut)
				data, addr = sock.recvfrom(bueyPackage.size)  
				unpackedData = bueyPackage.unpack(data)
				randomIdReceived = (unpackedData[0]).decode()
				print("Client: State: Buey packet received : ", unpackedData)
				waitingReply = False 
			except: 
				print("Client: State: Buey packet lost (time-out), resending...") 
				sock.sendto(lastSent, (UDP_IP, UDP_PORT))
		elif time.time() - timeCommStart >= sendFrequency:	
			if randomIdReceived == randomIdWanted:    
				lastSent, waitingReply, lastRID =  sendPackage()
				timeCommStart = time.time()
				randomIdWanted = carretaPackage.unpack(lastSent)[0].decode()
				print("Client : State: Packet sent successfully.")
			else: 
				print("Client : State: Random ID did not match, resending...")
				sock.sendto(lastSent, (UDP_IP, UDP_PORT)) 
				timeCommStart = time.time()
				waitingReply = True 
main()
