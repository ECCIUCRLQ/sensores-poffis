import struct
import sys
import queue
import threading
import csv

queue_size=1000

class Collectors:
	def initializer(interface_queue):
		
		csv_sensor_counter=0
		with open('identificadores.csv', 'r') as csv_file:
			csv_reader = csv.reader(csv_file,delimiter = ',')
			next(csv_reader)
			collectors_info=[]
			for line in csv_reader:
				if(line[0]==-1):
					break
				collectors_info.append(int(line[0]),int(line[1]),queue.Queue(queue_size),threading.Condition(),0)
				csv_sensor_counter+=1
			
			for n_collector_thread in range(csv_sensor_counter):
				collectors_info[n_collector_thread][4]=n_collector_thread
				thread=threading.Thread(target=self.collect, args =(n_collector_thread, collectors_info[n_collector_thread][2],interface_queue,collectors_info[n_collector_thread][3]) )
				thread.start
				
			return collectors_info;
		
		
	def collect(thread_id, collector_queue ,interface_queue, condition):
		while True:
			#The condition structure sends to sleep those threads that are not currently receiveng data 
			condition.aquire()
			if(collector_queue.empty()):
				condition.wait()
			data_card=[collector_queue.get(),thread_id]
			interface_queue.put(data_card)
			condition.release()
				
				
				
		
