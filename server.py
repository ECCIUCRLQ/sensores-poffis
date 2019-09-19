import binascii
import socket
import struct
import sys
import queue
import threading
import csv
from datetime import datetime

UDP_IP = "127.0.0.1"
UDP_PORT = 5009

carretaInt = struct.Struct('1s I 4s 1s I') 
bueyPack = struct.Struct('1s 4s')

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP				 
sock.bind((UDP_IP, UDP_PORT))
queue_size = 10000
packet_queue = queue.Queue(queue_size)
semaphore = threading.Semaphore(0)
lock = threading.Lock()
def recv_package():
	lastACK = 300
	while True:
		try:
			sock.settimeout(5)
			data, addr = sock.recvfrom(carretaInt.size)
			#print ('received message: {!r}',  format(binascii.hexlify(data)))
			unpackedData = carretaInt.unpack(data)
			#print ('unpacked: ', unpackedData)
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
			first_byte_sensorID = bytes_from_sensorID[3] 
			second_byte_sensorID = bytes_from_sensorID[2]
			third_byte_sensorID = bytes_from_sensorID[1]
			if(second_byte_sensorID > 0 and third_byte_sensorID > 0):	
				sensor_identification = first_byte_sensorID + (second_byte_sensorID + 256) + (third_byte_sensorID + (256 * 256))
			elif(second_byte_sensorID > 0):
				sensor_identification = first_byte_sensorID + (second_byte_sensorID + 256)
			elif(third_byte_sensorID > 0):
				sensor_identification = first_byte_sensorID + (third_byte_sensorID + (256 * 256))
			#print(team)
			#print(sensor_identification)
			#print(ACK)
			if(lastACK != ACK):
				newPackage = (randomID, sensorID)
				packedData = bueyPack.pack(*newPackage)
				#print(newPackage)
				sock.sendto(packedData, addr)
				lastACK = ACK
				package= [date,sensor_type,team,sensor_identification,data,0]
				lock.acquire
				if(sensor_type != 0):
					packet_queue.put(package)
					semaphore.release()
				lock.release
		except: #timeout: se perdio el cliente
			package = [0,0,0,0,0,0,1]
def main():
	thread = threading.Thread(target=recv_package)
	thread.start()
	while True:
		with open('identificadores.csv', 'r') as csv_file:
			csv_reader = csv.reader(csv_file,delimiter = ',')
			next(csv_reader)
			semaphore.acquire()
			lock.acquire
			package = packet_queue.get()
			lock.release
			timeout = package[5]
			if(timeout == 0):
				date = package[0]
				sensor_type = package[1]
				team = package[2]
				sensor_identification = package[3]
				data = package[4]
				teamID = ""
				sensor_typeID = ""
				for line in csv_reader:
					if(int(line[0]) == team):
						teamID = line[4]
					if(int(line[1]) == sensor_type):
						sensor_typeID = line[2]		
				print (datetime.utcfromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S'), sensor_typeID,teamID,sensor_identification,data)
			else:
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
