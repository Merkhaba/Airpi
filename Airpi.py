# The MIT License (MIT)

# Copyright (c) 2016 Nicholas Johnson

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import RPi.GPIO as GPIO
import time
import datetime
import Adafruit_DHT
import os

__author__ = "Nicholas Johnson <nejohnson2@gmail.com>"
__copyright__ = "Copyright (C) 2016 Nicholas Johnson"
__license__ = "MIT"
__version__ = "v1.0"

'''History
v1.0 - First Release
'''
	
class Shinyei(object):

	def __init__(self, pin):
		self.pin = pin 			# pin for GPIO connection
		GPIO.setup(self.pin, GPIO.IN)
		
	def _start(self):
		'''Set default values and 
		attach event detection'''
		self.lpo = 0				# duration of low pulses
		self.start_ltime = 0		# initialize to zero to prevent start with low pulse
		GPIO.add_event_detect(self.pin, GPIO.BOTH, self._get_lpo)

	def _reset(self):
		'''Remove event detection'''
		GPIO.remove_event_detect(self.pin)	# prevents an interrupt during the rest of the code		

	def _get_lpo(self, channel):
		'''Callback function when pin 
		changes	high or low'''

		current_time = time.time()	# get time when event happened

		if not GPIO.input(channel):
			'''Reading went low'''
			self.start_ltime = current_time					# start timer for low reading
		else:
			'''Reading went high'''
			if self.start_ltime != 0:
				duration = current_time - self.start_ltime		# add time that was low
				self.lpo += duration

	def _calc_ratio(self, duration):
		'''calculate ratio of low pulse time to total time'''
		if self.lpo != 0:
			ratio = float(self.lpo) / float(duration)		# calculate percentage of pulses being low
		else:
			ratio = 0

		return ratio

	def _calc_concentration(self, ratio):
		'''calculate particles per 0.01 cubic feet'''
		concentration = (1.1 * ratio**3) - (3.8 * ratio**2) + (520 * ratio) + 0.62

		return concentration

	def read(self, duration):
		'''Output results every 30s
		otherwise do nothing'''
		self._start()
		start_time = time.time()

		while time.time() - start_time < duration:
			pass			# do nothing 
		else:
			r = self._calc_ratio(duration)
			c = self._calc_concentration(r)

			self._reset()	# remove event detect
			return [self.lpo, r, c]
		
class MQAirSensor(object):
    
    def __init__(self): 
        self.SPICLK = 18
        self.SPIMISO = 23
        self.SPIMOSI = 24 
        self.SPICS = 25
        GPIO.setup(self.SPIMOSI, GPIO.OUT) 
        GPIO.setup(self.SPIMISO, GPIO.IN) 
        GPIO.setup(self.SPICLK, GPIO.OUT) 
        GPIO.setup(self.SPICS, GPIO.OUT)

        # read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
    def readadc(self, adcnum): 
         if ((adcnum > 7) or (adcnum < 0)):
          return -1 

         GPIO.output(self.SPICS, True) 
         GPIO.output(self.SPICLK, False)  # start clock low 
         GPIO.output(self.SPICS, False)   # bring CS low
         commandout = adcnum
         commandout |= 0x18 # start bit + single-ended bit 
         commandout <<= 3 # we only need to send 5 bits here

         for i in range(5):
          if (commandout & 0x80):
           GPIO.output(self.SPIMOSI, True) 
          else:
           GPIO.output(self.SPIMOSI, False) 
          commandout <<= 1
          GPIO.output(self.SPICLK, True) 
          GPIO.output(self.SPICLK, False)

         adcout = 0

         # read in one empty bit, one null bit and 10 ADC bits 
         for i in range(12):
          GPIO.output(self.SPICLK, True) 
          GPIO.output(self.SPICLK, False) 
          adcout <<= 1
          if (GPIO.input(self.SPIMISO)):
           adcout |= 0x1 

         GPIO.output(self.SPICS, True)
         adcout >>= 1 # first bit is 'null' so drop it 
         return adcout

        
# Main loop
if __name__ == '__main__':
    sensor = Adafruit_DHT.DHT22
    pinDHT = 4
    GPIO.setmode(GPIO.BCM)
    mq = MQAirSensor()
    t = Shinyei(27)
    while True:
        l, r ,c = t.read(30)
        temp, hum = Adafruit_DHT.read_retry(sensor,pinDHT)
        read_pinMQ135 = mq.readadc(0) * 3.3 / 1024.0
        read_pinMQ2 = mq.readadc(1) * 3.3 / 1024.0
        raspberry_temp = os.popen("vcgencmd measure_temp").readline()
        print("[{0}] Temp={3:0.1f}*C  Humidity={4:0.1f}%  Ratio={1:0.6f}  Concentration={2:0>4.2f} pcs per 0.01 cubic foot  MQ135={5:0.2f} Volts  MQ2={6:0.2f} Volts Raspberry Temp={7}".format(datetime.datetime.now(),r,c,hum,temp,read_pinMQ135,read_pinMQ2,raspberry_temp))
        time.sleep(15)
    GPIO.cleanup()	



