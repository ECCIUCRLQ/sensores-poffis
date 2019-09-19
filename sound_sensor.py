# Code taken from adafruit circuit library, Author: Tony DiCola
# Modified by team Poffis
# License: Public Domain

# Import the ADS1x15 module.
import Adafruit_ADS1x15

# Create an ADS1115 ADC (16-bit) instance.
adc = Adafruit_ADS1x15.ADS1115()

# Sensibilidad del sensor de sonido.
GAIN = 1

class SoundSensor:
    
    """
    Method that returns on demand the actual read of noise.
    Parameter:
        user_gain: Sensibility of the sensor. Use the table below for
        detailed info.
    Detailed info
    Choose a gain of 1 for reading voltages from 0 to 4.09V.
    Or pick a different gain to change the range of voltages that are read:
      - 2/3 = +/-6.144V
      -   1 = +/-4.096V
      -   2 = +/-2.048V
      -   4 = +/-1.024V
      -   8 = +/-0.512V
      -  16 = +/-0.256V
    """
    def getSoundData(self):
      return adc.read_adc(0,GAIN)
    


