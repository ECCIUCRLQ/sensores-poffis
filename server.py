import binascii
import socket
import struct
import sys

UDP_IP = "10.1.138.42" #"10.1.138.34"
UDP_PORT = 5000

#unpacker = struct.Struct('1s f 4s 1s 7s')
unpacker = struct.Struct('1s f 4s 1s f')

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock2 = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP					 
sock.bind((UDP_IP, UDP_PORT))

while True:
	data, addr = sock.recvfrom(unpacker.size)
	print ('received message: {!r}',  format(binascii.hexlify(data)))
	unpacked_data = unpacker.unpack(data)
	print ('unpacked: ', unpacked_data)
	#if(unpacked_data[4].decode() == "Carreta"):

	print(unpacked_data)
	#newPackage = (unpacked_data[0], unpacked_data[1], unpacked_data[2], unpacked_data[3], b"Buey")
	#packed_data = unpacker.pack(*newPackage)
	#print(newPackage)
		#sock2.sendto(packed_data, (UDP_IP, 5000))
	#socket.sendto(unpacked_data, (UDP_IP, UDP_PORT))
