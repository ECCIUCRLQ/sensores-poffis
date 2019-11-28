import struct
import queue
import threading
import time
import socket

def test():
    TCP_IP = '192.168.1.2'
    TCP_PORT = 6011
    BUFFER_SIZE = 1024
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    values = (bytearray([2]),bytearray([1]),5,1,2,3,4,5)
    packetStruct = struct.Struct('1s 1s I I I I I I')
    packet = packetStruct.pack(*values)
    s.send(packet)
    s.close()
'''from time import sleep 
    sleep(10)
    #values = (bytearray([2]),bytearray([1]),5,1,2,3,4,5)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    values = (bytearray([3]),bytearray([1]),5,1,2,3,4,5)
    packetStruct = struct.Struct('1s 1s I I I I I I')
    packet = packetStruct.pack(*values)
    s.send(packet)
    print(packet)'''
    

test()
