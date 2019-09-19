import binascii
import socket
import struct
import sys
import queue
import threading
import csv
from datetime import datetime

UDP_IP = "10.1.138.34"
UDP_PORT = 5003
#struct datos recibidos-datos enviados
carretaInt = struct.Struct('1s I 4s 1s I') 
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
			data = receive_data[4]
			ACK = struct.unpack('>H',b'\x00' + randomID)[0]
			sensor_type = struct.unpack('>H',b'\x00' + sensor_type)[0]
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
				#crea y reenvia el ACK
				newPackage = (randomID, sensorID)
				packedData = bueyPack.pack(*newPackage)
				#print(newPackage)
				sock.sendto(packedData, addr)
				#actualiza el ACK para ver si es un paquete repetido
				lastACK = ACK
				package= [date,sensor_type,team,sensor_identification,data,0]
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
	while True:
		#abre el archivo csv en modo lectura
		with open('identificadores.csv', 'r') as csv_file:
			csv_reader = csv.reader(csv_file,delimiter = ',')
			next(csv_reader)
			semaphore.acquire()
			#cierra el mutex, saca el paquete respectivo de la cola, y lo vuelve a abrir
			lock.acquire
			package = packet_queue.get()
			lock.release
			#Si hubo un timeout, el servidor termina su ejecución, sino imprime el paquete
			timeout = package[5]
			if(timeout == 0):
				date = package[0]
				sensor_type = package[1]
				team = package[2]
				sensor_identification = package[3]
				data = package[4]
				teamID = ""
				sensor_typeID = ""
				#obtiene sus equivalentes según el archivo CSV
				for line in csv_reader:
					if(int(line[0]) == team):
						teamID = line[4]
					if(int(line[1]) == sensor_type):
						sensor_typeID = line[2]		
				print (datetime.utcfromtimestamp(date-21600).strftime('%Y-%m-%d %H:%M:%S'), sensor_typeID,teamID,sensor_identification,data)
			else:
				print("cliente caido")
				break

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
