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


# Creacion del socket, definicion de IP y puerto del servidor.
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
UDP_IP = "127.0.0.1"			 
UDP_PORT = 5002				 

# SensorID = TEAM_ID + MOVEMENT_SENSOR || TEAM_ID + SOUND_SENSOR
TEAM_ID = 6
MOVEMENT_SENSOR = 1
SOUND_SENSOR = 2

# Type = MOVEMENT_DATA_TYPE || SOUND_DATA_TYPE || KEEP_ALIVE
MOVEMENT_DATA_TYPE = 9
SOUND_DATA_TYPE = 7
KEEP_ALIVE_TYPE = 0

# Creacion de un queue donde se guardan los paquetes a enviar.
QUEUE_SIZE = 10000
packetsQueue = queue.Queue(QUEUE_SIZE)

# Formato del paquete a enviar.
carretaPackage = struct.Struct('1s I 4s 1s I') 

# Formato del paquete a recibir.
bueyPackage = struct.Struct('1s 4s')

# Frecuencia de envío de paquetes y timeout (en segundos).
sendFrequency, timeOut = 1.0, 5.0

# Mutex.
lock = threading.Lock()

def pushPacketToQueue(movementSensor, soundSensor):
	while True:
		time.sleep(1)
		lock.acquire()
		packetsQueue.put( createPackage(MOVEMENT_SENSOR, movementSensor) )
		packetsQueue.put( createPackage(SOUND_SENSOR, soundSensor) )
		lock.release()

def createPackage(sensorType, sensorInstance = None):
	if sensorType == MOVEMENT_SENSOR :  # Se crea un paquete con un dato del sensor de movimiento.
		values = ( random.choice(string.ascii_letters).encode(), int(time.time()), bytearray([TEAM_ID, 0, 0, MOVEMENT_SENSOR]), chr(MOVEMENT_DATA_TYPE).encode(), MovementSensor.getMovementData(MovementSensor) )
	elif sensorType == SOUND_SENSOR : # Se crea un paquete con un dato del sensor de sonido.
		values = ( random.choice(string.ascii_letters).encode(), int(time.time()), bytearray([TEAM_ID, 0, 0, SOUND_SENSOR]), chr(SOUND_DATA_TYPE).encode(),  SoundSensor.getSoundData(SoundSensor) )
	else:								# Se crea un paquete de KEEP ALIVE. 
		values = ( random.choice(string.ascii_letters).encode(), int(time.time()), bytearray([TEAM_ID, 0, 0, 0]), chr(KEEP_ALIVE_TYPE).encode(), 0)
	return carretaPackage.pack(*values) 
		
def sendPackage():	
	if not packetsQueue.empty() : # Si hay un paquete disponible en la cola lo envía.
		lock.acquire()
		packet = packetsQueue.get()
		lock.release()
	else: # Si no envía un paquete de tipo KEEP ALIVE, para indicar que el cliente sigue vivo pero no hay paquetes por enviar.
		packet = createPackage(KEEP_ALIVE_TYPE)
	
	sock.sendto(packet, (UDP_IP, UDP_PORT))
	return packet, True

def main():
	movementSensor = MovementSensor()
	movementSensor.throw_batarang()
	soundSensor = SoundSensor()
	# Crea un thread que ejecuta la subrutina pushPacketToQueue cada segundo.
	threading.Thread(target=pushPacketToQueue, args = (movementSensor, soundSensor) ).start()
	timeCommStart = time.time()
	lastSent, waitingReply =  sendPackage()
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
				lastSent, waitingReply =  sendPackage()
				timeCommStart = time.time()
				randomIdWanted = carretaPackage.unpack(lastSent)[0].decode()
				print("Client : State: Packet sent successfully.")
			else: 
				print("Client : State: Random ID did not match, resending...")
				sock.sendto(lastSent, (UDP_IP, UDP_PORT)) 
				timeCommStart = time.time()
				waitingReply = True 
main()
