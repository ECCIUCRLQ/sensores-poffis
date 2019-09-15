

#values = adc.read_adc(i, gain=1)

import RPi.GPIO as GPIO
import time

>>>check_point.__doc__
	"""
	check_point(length, frequency, lectures_queue)
		Method wich manages an ultrasonic sensor. Provides lectures approximations
		of human presence inside a area.
	Parameters:
		length: Size of the access entrance to the area
		frequency: how often adds a lecture to the queue
		lectures_queue: structure wich shares information with the other threads
	"""
	
def check_point(length, frequency, lectures_queue)
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
		
