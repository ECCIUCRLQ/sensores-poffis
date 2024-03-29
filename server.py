import binascii
import socket
import struct
import sys
import queue
import threading
import csv
from datetime import datetime
from interface import Interface
from collectors import Collectors
from plotter import Plotter
from memory import MemoryManager

UDP_IP = "10.1.138.34"
UDP_PORT = 5015
#struct datos recibidos-datos enviados
carretaInt = struct.Struct('1s I 4s 1s I')
carretaFloat = struct.Struct('1s I 4s 1s f') 
bueyPack = struct.Struct('1s 4s')

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP				 
sock.bind((UDP_IP, UDP_PORT))
#tamaño de cola de mensajes sin imprimir
queue_size = 10000
packet_queue = queue.Queue(queue_size)
semaphore = threading.Semaphore(0)
lock = threading.Lock()
#recibir paquete e insertar en la cola de paquetes recibidos
def recv_package():
	lastACK = 300
	while True:
		try:
			#si el cliente no responde en 15 segundo, murio el cliente
			sock.settimeout(180)
			data, addr = sock.recvfrom(carretaInt.size)
			#print ('received message: {!r}',  format(binascii.hexlify(data)))
			unpackedData = carretaInt.unpack(data)
			#print ('unpacked: ', unpackedData)
			#tranformar lo recibido en paquetes, en variables leibles, por ejemplo pasar 1 byte a un int o 3 bytes a int
			receive_data = list(unpackedData)
			randomID = receive_data[0]
			date = receive_data[1]
			sensorID = receive_data[2]
			sensor_type = receive_data[3]
			sensor_type = struct.unpack('>H',b'\x00' + sensor_type)[0]
			#print("SensorID:", sensorID, " sensorType: ",sensor_type)
			#print(sensor_type)
			if((sensor_type) ==  6 or sensor_type == 8):
				unpackedData = carretaFloat.unpack(data)
				receive_data = list(unpackedData)
			data = receive_data[4]
			#print(type(data))
			if((sensor_type) ==  2 or sensor_type == 1 or sensor_type == 3 or sensor_type == 4 or sensor_type == 5 ):
				if data != 0:
					data = 1
			#print("Despues")
				
			ACK = struct.unpack('>H',b'\x00' + randomID)[0]	
			#print(type(sensor_type))
			bytes_from_sensorID = bytes(sensorID)
			team = bytes_from_sensorID[0]
			#bytes de sensorID sin incluir la parte de equipo(los 3 bytes)
			first_byte_sensorID = bytes_from_sensorID[3] 
			second_byte_sensorID = bytes_from_sensorID[2]
			third_byte_sensorID = bytes_from_sensorID[1]
			if(second_byte_sensorID > 0 and third_byte_sensorID > 0):	
				sensor_identification = first_byte_sensorID + (second_byte_sensorID + 256) + (third_byte_sensorID + (256 * 256))
			elif(second_byte_sensorID > 0):
				sensor_identification = first_byte_sensorID + (second_byte_sensorID + 256)
			elif(third_byte_sensorID > 0):
				sensor_identification = first_byte_sensorID + (third_byte_sensorID + (256 * 256))
			else:
				sensor_identification = first_byte_sensorID
			#print(team)
			#print(sensor_identification)
			#print(ACK)
			#revisa que no sea un ACK repetido, si lo es simplemente lo ignora
			if(lastACK != ACK):
				#print('ACK')
				#crea y reenvia el ACK
				newPackage = (randomID, sensorID)
				packedData = bueyPack.pack(*newPackage)
				#print(newPackage)
				sock.sendto(packedData, addr)
				#actualiza el ACK para ver si es un paquete repetido
				lastACK = ACK
				package = [date,team,sensor_identification,sensor_type,data,0]
				#entra a un mutex para añadir a la cola
				lock.acquire
				#si no es un keep alive, añade el paquete a la cola de paquetes
				if(sensor_type != 0):
					packet_queue.put(package)
					#señala con un semáforo que hay un nuevo paquete por ser leído
					semaphore.release()
				lock.release
			else:
				print(ACK)
		except: #timeout: se perdio el cliente
			package = [0,0,0,0,0,0,1]
def main():
	
	thread = threading.Thread(target=recv_package)
	thread.start()
	### Leer cuantos sensores hay conectados para poder realizar el handshake(malloc mágico)
	### Crear barrera con contador = cuantos sensores hay
	### Crear cola para cada thread
	### Crear semaforo para cada cola de rocolectores
	### Crear threads recolectores (se envía de parámetro su cola y su identificador respectivo)
	#abre el archivo csv en modo lectura
	interface_queue = queue.Queue(queue_size)
	collectors = Collectors()
	collectors_info = collectors.initializer(interface_queue)
	
	memoryManager = MemoryManager()

	plotter = Plotter()

	#Por cuestiones de comodidad se inicializa acá pero no se usa posteriormente.
	interface = Interface()
	#plotter.initializer(interface)
	interface.initializer(interface_queue, collectors_info, memoryManager, plotter)
	
	while True:		
		with open('identificadores.csv', 'r') as csv_file:
			csv_reader = csv.reader(csv_file,delimiter = ',')
			next(csv_reader)
			next(csv_reader)
			semaphore.acquire()
			#cierra el mutex, saca el paquete respectivo de la cola, y lo vuelve a abrir
			lock.acquire
			package = packet_queue.get()
			lock.release
			#Si hubo un timeout, el servidor termina su ejecución; si no, imprime el paquete.
			timeout = package[5]
			if(timeout == 0):
				#Multiplexor: Envia el paquete a su cola correspondiente
				#print(package)
				for line in collectors_info:
					plot_data=[package[0],package[4]]
					#print(plot_data)
					"""print(line[0], package[1])
					print(line[1], package[2])
					print(line[2], package[3])"""
					if(line[0] == package[1] and line[2] == package[2] and line[1] == package[3]):
						#print("entre")
						line[4].acquire()
						line[3].put(plot_data)
						line[4].notify()
						line[4].release()
			else:
				print("cliente caido")
				break

main()



		
		


def bytes_to_int(bytes):
	result = 0
	for b in bytes:
		result = result * 256 + int(b)
	return result
	

"""Protocolo del cliente al servidor	
Random ID	1 byte
Date	4 bytes
SensorID	4 bytes
Tipo de sensor	1 byte
Datos	
	
Protocolo servidor-cliente	
Random ID	1 byte
Sensor ID	4 bytes"""
