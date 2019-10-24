import socket
import binascii
import struct
import sys
import time
import random
import string
import threading
import queue
#import RPi.GPIO as GPIO # DESCOMENTAR

# Sensor constants.
PATH_LENGTH = 50
FREQUENCY = 1

# Sensor data queue.
QUEUE_SIZE = 10000
lectures_queue = queue.Queue(QUEUE_SIZE) 

class MovementSensor:
	"""
	Routine of constant motion checking.Method wich manages an ultrasonic 
	sensor. Provides approximationsof human presence inside a area.
	Parameters:
		self:implicit object provided  by python (Kind of "this") when 
		make a call from other file.
		path_length: Size of the access path to the area of study
		frequency: how often adds a lecture to the queue

	"""
	
	def batarang_thrower(self):
		trig = 23
		echo = 24

		GPIO.setmode(GPIO.BCM)
		GPIO.setup(trig, GPIO.OUT)
		GPIO.setup(echo, GPIO.IN)

		people_counter = 0
		chrono_start = time.time()
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
			if distancia < PATH_LENGTH:
				people_counter += 1
				
			if time.time()-chrono_start >= FREQUENCY:
				lectures_queue.put(people_counter)
				chrono_start = time.time()
	"""
	Return the values of the queue to the client
	Parameter 
		self:implicit object provided  by python (Kind of "this") when 
		make a call from other file.
		
	"""			
	def getMovementData(self):
		return 777
		#return lectures_queue.get(True)
	
	"""
	Initializer of the thread that execute lectures constantly
	Parameters:
			self:implicit object provided  by python (Kind of "this") when 
			make a call from other file.
			path_length: Size of the access path to the area of study
			frequency: how often adds a lecture to the queue
	
	"""
	def throw_batarang(self):
		batarang = threading.Thread(target=self.batarang_thrower)
		batarang.start()
		
			

