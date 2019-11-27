import struct
import queue
import threading
import time
import socket

def test():
    TCP_IP = '10.0.2.15'
    TCP_PORT = 6000
    BUFFER_SIZE = 1024
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    values = (bytearray([2]),bytearray([1]),5,1,2,3,4,5)
    packetStruct = struct.Struct('1s 1s I I I I I I')
    packet = packetStruct.pack(*values)
    s.send(packet)
    #values = (bytearray([2]),bytearray([1]),5,1,2,3,4,5)
    print(packet)
    

test()
