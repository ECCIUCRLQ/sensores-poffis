GAIN 1

#values = adc.read_adc(i, gain=GAIN)

import RPi.GPIO as GPIO
import time
TRIG = 23
ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)


def check_point(length)
	GPIO.output(TRIG, GPIO.LOW)
	time.sleep(2)
	GPIO.output(TRIG, GPIO.HIGH)
	time.sleep(0.00001)
	GPIO.output(TRIG, GPIO.LOW)
	counter=0
	while True:

		while True:
			if GPIO.input(ECHO) == GPIO.HIGH:
				pulso_inicio = time.time()
				break

		while True:
			if GPIO.input(ECHO) == GPIO.LOW:
				pulso_fin = time.time()
				break
		duracion = pulso_fin - pulso_inicio
		distancia = (34300 * duracion) / 2
		if distancia < length
			counter= counter + 1
