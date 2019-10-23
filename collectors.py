import struct
import sys
import queue
import threading
import csv 

queue_size=1000


class Collectors:
	#Recibe la cola a donde debe enviar sus paquetes
	def initializer(self, interface_queue):
		
		#Se usa para saber cuantos thread crear 
		csv_sensor_counter=0
		
		#Abrimos el csv para crear la tabla de informacion de los recolectores
		with open('identificadores.csv', 'r') as csv_file:
			csv_reader = csv.reader(csv_file,delimiter = ',')
			#Saltamos encabezados del csv y 
			next(csv_reader)
			next(csv_reader)
			#El siguiente for crea la matriz(tabla) donde se va a guardar la informacion
			#de los recolectores
			#Cada fila de la matriz es un recolector y lucirian asi:
			# [team, sensor_type, collector_queue, condition_variable, thread_id]
			# **team: equipo que al que pertenece el sensor
			# **sensor_type: tipo de sensor
			# **collector_queue: Cola exclusiva del recolector
			# **condition_variable: Esta condicion de variable manda a dormir a los threads
			# cuando sus colas estan vacias
			# **thread_id: thread en el que esta corriendo el recolector
			
			collectors_info=[]
			for line in csv_reader:
				#El thread_id se asigna en el siguiente for, por eso es 0.
				row = [int(line[0]),int(line[1]),queue.Queue(queue_size),threading.Condition(),0]
				collectors_info.append(row)
				csv_sensor_counter+=1
				print(csv_sensor_counter)
			
			
			
			#Crea un thread por cada entrada de la matriz anterior
			for n_collector_thread in range(csv_sensor_counter-1):
				collectors_info[n_collector_thread][4] = n_collector_thread
				thread = threading.Thread(target=self.collect, args =(n_collector_thread, collectors_info[n_collector_thread][2],interface_queue,collectors_info[n_collector_thread][3]) )
				thread.start()
			
			#Se le devuelve al servidor para que pueda multiplexar los paquetes	
			return collectors_info;
		
		
	def collect(self, thread_id, collector_queue ,interface_queue, condition):
		while True:
			#Esta seccion es la de recoleccion y canalizacion a la cola de la interfaz
			#Si la cola esta vacia el thread no consume procesamiento
			condition.acquire()
			if(collector_queue.empty()):
				condition.wait()
			#Se le pasa el thread_id a interfaz para que sea mas sencillo identificar los paquetes
			data_card = [collector_queue.get(),thread_id]
			interface_queue.put(data_card)
			condition.release()
				
				
				
		
