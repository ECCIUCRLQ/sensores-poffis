import socket
import binascii
import struct
import sys
import time
import random
import string
import threading
import queue
import RPi.GPIO as GPIO

lectures_queue = queue.Queue(100) 

class batarang_class:
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
	
	def batarang_thrower(self,path_length, frequency):
		trig = 23
		echo = 24

		GPIO.setmode(GPIO.BCM)
		GPIO.setup(trig, GPIO.OUT)
		GPIO.setup(echo, GPIO.IN)

		people_counter=0
		chrono_start=time.time()
		while True:
			GPIO.output(trig, GPIO.LOW)
			time.sleep(0.5)
			GPIO.output(trig, GPIO.HIGH)
			time.sleep(0.00001)
			GPIO.output(trig, GPIO.LOW)
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
			if distancia < path_length:
				people_counter += 1
				
			if time.time()-chrono_start>=frequency:
				lectures_queue.put(people_counter)
				chrono_start=time.time()
				
	def catch_batarang(self):
		return lectures_queue.get()
		
	def throw_batarang(self, path_length, frequency):
		batarang = threading.Thread(target=self.batarang_thrower, args=(path_length, frequency))
		batarang.start()
		
			

