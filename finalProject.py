#!/usr/bin/env python

import RPi.GPIO as GPIO
from gpiozero import Button
import time
from datetime import datetime

import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

"""
When I asked myself "what doomed this project?"
I found that the answer lies beneath this line
"""
import threading

#import gspread
from oauth2client.service_account import ServiceAccountCredentials
#from pprint import pprint
from googleapiclient import discovery

my_path = "/home/pi/src/entr390/"

"""
Button intialization
"""
button1 = Button(2)
button2 = Button(3)

"""
Buzzer intialization
"""
BuzzerPin = 4


CL = [0, 131, 147, 165, 175, 196, 211, 248] # Low C Note Frequency
CM = [0, 262, 294, 330, 350, 393, 441, 495] # Middle C Note Frequency
CH = [0, 525, 589, 661, 700, 786, 882, 990] # High C Note Frequency

song_1 = [ CM[3], CM[5], CM[6], CM[3], CM[2], CM[3], CM[5], CM[6], # Sound Notes 1
CH[1], CM[6], CM[5], CM[1], CM[3], CM[2], CM[2], CM[3],
CM[5], CM[2], CM[3], CM[3], CL[6], CL[6], CL[6], CM[1],
CM[2], CM[3], CM[2], CL[7], CL[6], CM[1], CL[5] ]

beat_1 = [ 1, 1, 3, 1, 1, 3, 1, 1, # Beats of song 1, 1 means 1/8 beats
1, 1, 1, 1, 1, 1, 3, 1,
1, 3, 1, 1, 1, 1, 1, 1,
1, 2, 1, 1, 1, 1, 1, 1,
1, 1, 3 ]

song_2 = [ CM[1], CM[1], CM[1], CL[5], CM[3], CM[3], CM[3], CM[1], # Sound Notes 2
CM[1], CM[3], CM[5], CM[5], CM[4], CM[3], CM[2], CM[2],
CM[3], CM[4], CM[4], CM[3], CM[2], CM[3], CM[1], CM[1],
CM[3], CM[2], CL[5], CL[7], CM[2], CM[1] ]

beat_2 = [ 1, 1, 2, 2, 1, 1, 2, 2, # Beats of song 2, 1 means 1/8 beats
1, 1, 2, 2, 1, 1, 3, 1,
1, 2, 2, 1, 1, 2, 2, 1,
1, 2, 2, 1, 1, 3 ]

GPIO.setmode(GPIO.BCM) # Numbers GPIOs by physical location
GPIO.setup(BuzzerPin, GPIO.OUT) # Set pins' mode is output
# global Buzz # Assign a global variable to replace GPIO.PWM
Buzz = GPIO.PWM(BuzzerPin, 440) # 440 is initial frequency.
Buzz.start(50) # Start BuzzerPin pin with 50% duty ration
Buzz.stop()

"""
Display initialization
"""
# Raspberry Pi hardware SPI config:
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0

# Hardware SPI usage:
disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))

# Software SPI usage (defaults to bit-bang SPI interface):
#disp = LCD.PCD8544(DC, RST, SCLK, DIN, CS)

# Initialize library.
disp.begin(contrast=60)

# Clear display.
disp.clear()
disp.display()

# Load image and convert to 1 bit color.
#image = Image.open('happycat_lcd.ppm').convert('1')

# Alternatively load a different format image, resize it, and convert to 1 bit color.
image = Image.open(my_path + 'sun.png').resize((LCD.LCDWIDTH, LCD.LCDHEIGHT), Image.ANTIALIAS).convert('1')

# Display image.
disp.image(image)
disp.display()

# Font
# font = ImageFont.load_default()
font = ImageFont.truetype(my_path + "arial_narrow_7.ttf", 36)

draw = ImageDraw.Draw(image)

"""
Google Spreadsheet initialization
"""
try:
	scope = 'https://www.googleapis.com/auth/spreadsheets'
	credentials = ServiceAccountCredentials.from_json_keyfile_name(my_path + 'smart-alarm-clock-key.json', scope)
	spreadsheet_id = "1M6Twx3Z-cidC60E3CRULjGFV1TP5jfTf-SQzLcGyDR0"
	service = discovery.build('sheets', 'v4', credentials=credentials)
	request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range="B1:L7")
except:
	print "No connection, sad times"

def loop():
	try:
		times_dict = request.execute()
	except:
		print("No alarms found")
	blink = False
	press_count = 0
	while True:
		blink = not blink
		current_time = str(datetime.now().time())
		current_time = sliceTime(current_time)
		day = datetime.today().weekday()
		try:
			#print("Current time")
			#print(current_time)
			#print("Today's alarms")
			#print(times_dict["values"][day])
			for time_index in range(len(times_dict["values"][day]) - 1, -1, -1):
				if times_dict["values"][day][time_index] == current_time:
					buzz_thread = threading.Thread(target=playBuzzer)
					buzz_thread.setDaemon(True)
					buzz_thread.start()
					times_dict["values"][day].pop(time_index)
		except:
			print("Nothing to check for")
		displayTime(blink)
		if button2.is_pressed:
			press_count += 1
			if press_count == 4:
                                draw.rectangle((0, 0, 83, 47), outline = 255, fill = 255)
				try:
					times_dict = request.execute()
                                        image = Image.open(my_path + 'success.png').resize((LCD.LCDWIDTH, LCD.LCDHEIGHT), Image.ANTIALIAS).convert('1')
				except:
					print("No alarms found")
					image = Image.open(my_path + 'failure.png').resize((LCD.LCDWIDTH, LCD.LCDHEIGHT), Image.ANTIALIAS).convert('1')
				disp.image(image)
                                disp.display()
		else:
			if press_count > 0 and press_count < 4:
				try:
					times_dict["values"][day] = []
					image = Image.open(my_path + 'sun.png').resize((LCD.LCDWIDTH, LCD.LCDHEIGHT), Image.ANTIALIAS).convert('1')
                                        disp.image(image)
                                        disp.display()
				except:
					"No times to clear"
			press_count = 0
		time.sleep(1)

def destroy():
	Buzz.stop() # Stop the BuzzerPin
	GPIO.output(BuzzerPin, 1) # Set BuzzerPin pin to High
	# The RaspberryPi complained about me trying to cleanup resources! Unbelievable
	# GPIO.cleanup() # Release resource

def playBuzzer():
	global isBlinking
	isBlinking = True
	button_thread = threading.Thread(target=checkForButton)
	button_thread.setDaemon(True)
	button_thread.start()
	Buzz.start(50)
	print 'Playing song 1...\n'
	for i in range(1, len(song_1)): # Play song 1
		if button_thread.isAlive():
			Buzz.ChangeFrequency(song_1[i]) # Change the frequency along the song note
			time.sleep(beat_1[i] * 0.5) # delay a note for beat * 0.5s
		else:
			isBlinking = False
			Buzz.stop()
			return
	time.sleep(1) # Wait a second for next song.

	print 'Playing song 2...\n'
	for i in range(1, len(song_2)): # Play song 1
		if button_thread.isAlive():
			Buzz.ChangeFrequency(song_2[i]) # Change the frequency along the song note
			time.sleep(beat_2[i] * 0.5) # delay a note for beat * 0.5s
		else:
			isBlinking = False
			Buzz.stop()
			return
	isBlinking = False
	Buzz.stop()

def checkForButton():
	while (not button1.is_pressed and not button2.is_pressed):
		time.sleep(0.1)
	print 'Alarm stopped'

def displayTime(blink):
	global isBlinking
	text = str(datetime.now().time())
	text = sliceTime(text)
	hour = text[0:2]
	if int(hour) > 12:
		hour = str(int(hour) - 12)
	text = hour + text[2:len(text)]
	if isBlinking and blink:
		text = ""
	x_coord = 10
	if len(text) == 4:
            x_coord += 7
	draw.rectangle((0, 0, 83, 47), outline = 255, fill = 255)
	draw.text((x_coord, 10), text, font=font, fill=0)
	disp.image(image)
	disp.display()

def sliceTime(time):
	# hour = time[0:2]
	# if int(hour) > 12:
	#	hour = str(int(hour) - 12)
	#time = hour + time[2:len(time)]
	dotIndex = 0
	for i in range(len(time)):
		if (time[i] == "."):
			dotIndex = i
			break
	return time[0:dotIndex - 3]

isBlinking = False

if __name__ == '__main__': # Program start from here
	print("Press Ctrl+C to quit")
	try:
		loop()
	except KeyboardInterrupt: # When 'Ctrl+C' is pressed, the child program destroy() will be executed.
		destroy()
