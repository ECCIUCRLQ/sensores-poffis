import socket
import binascii
import struct
import sys
import time
import random
import string
import RPi.GPIO as GPIO
import threading
import queue

#######################Ads conversor libraries##########################
"""
Important, libraries must be installed manually in the raspeberry. Follow=
https://learn.adafruit.com/adafruit-4-channel-adc-breakouts/python-circuitpython
or
https://howchoo.com/g/mdzlytkyzgf/how-to-install-a-potentiometer-on-a-raspberry-pi
"""
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
########################################################################

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
UDP_IP = "192.168.0.11"			  # Destino
UDP_PORT = 5000				  # Destino
UDP_IP_CLIENT = "10.1.138.34"  		  # IP Cliente - espera respuesta del server
UDP_PORT_SERVER_REPLY = 5005		  # Port en el que viene la respuesta del server
sock2.bind((UDP_IP_CLIENT, UDP_PORT_SERVER_REPLY)) # Bind para respuesta del server
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



"""
	Routine of constant motion checking.	
	batarang_thrower(path_length, frequency, lectures_queue)
	Method wich manages an ultrasonic sensor. Provides approximations
	of human presence inside a area.
	Parameters:
		path_length: Size of the access path to the area of study
		frequency: how often adds a lecture to the queue
		lectures_queue: structure wich shares information with the other threads

"""
	
def batarang_thrower(path_length, frequency, lectures_queue)
	trig = 23
	echo = 24

	GPIO.setmode(GPIO.BCM)
	GPIO.setup(trig, GPIO.OUT)
	GPIO.setup(echo, GPIO.IN)
	GPIO.output(trig, GPIO.LOW)
	time.sleep(2)
	GPIO.output(trig, GPIO.HIGH)
	time.sleep(0.00001)
	GPIO.output(trig, GPIO.LOW)
	people_counter=0
	chrono_start=time.time()
	while True:
		while True:
			if GPIO.input(echo) == GPIO.HIGH:
				pulso_inicio = time.time()
				break

		while True:
			if GPIO.input(echo) == GPIO.LOW:
				pulso_fin = time.time()
				break
		duracion = pulso_fin - pulso_inicio
		distancia = (34300 * duracion) / 2
		if distancia < length
			people_counter += 1
			
		if time.time()-chrono_start>=frequency:
			lectures_queue.put(people_counter)
			chrono_start=time.time()
		

def main():
	##########################Sensors init##############################
	#Batarang
	path_length=50
	frecuency=1
	lectures_queue = queue.Queue(100) 
	batarang = threading.Thread(target=batarang_thrower, args=(path_length, frecuency,lectures_queue))
	batarang.start()
	time.sleep(2) #Sensor config time
	
	#Sound sensor
	i2c = busio.I2C(board.SCL, board.SDA)
	ads = ADS.ADS1115(i2c)
	
	"""
	Read sound sensor
		value = AnalogIn(ads, ADS.P%)
		%: stands for the number of the signal attached pin
	Read from queue (ultrasonic_sensor)
		value = lectures_queue.get()
	"""
	####################################################################
	ridReceived = ''  
	timeCommStart, timeRIDStart = time.time(), time.time()
	lastSent, ridWanted, waitingReply = sendPackage(hex(0), "Carreta", sock) # tipo y data viene del sensor
	while True:
		if waitingReply == True: 
			if time.time() - timeRIDStart <= timeRIDLimit: # Si aún estoy dentro del tiempo.
				data, addr = sock2.recvfrom(20)  
				unpackedData = packer1.unpack(data)
				ridReceived = (unpackedData)[0].decode()
				print("Recibi buey:", unpackedData)
				waitingReply = False 
			else:  # Si sucede un timeout.
				print("Random ID was not received. Resending last packet.") 
				print(time.time() - timeRIDStart)
				sock.sendto(lastSent, (UDP_IP, UDP_PORT)) # Ya esta empacado, no ocupa casos
				timeCommStart, timeRIDStart = time.time(), time.time()
		else:	
			if ridReceived == ridWanted:    # Un paquete fue recibido, se verifica si es del deseado mediante el ACK. 
				print("Packet sent.")
				print(time.time() - timeCommStart)
				lastSent, ridWanted, waitingReply = sendPackage(hex(0) , "Carreta", sock) # Tipo y data viene del sensor
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
