GAIN 1

# Main loop.
while True:
	values = [0]*4
	for i in range(4):
		values[i] = adc.read_adc(i, gain=GAIN)
	time.sleep(0.5)
