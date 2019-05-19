
import RPi.GPIO as GPIO
from time import sleep
import datetime
from firebase import firebase
import Adafruit_DHT
from PMS7003 import PMS7003 
import serial

import urllib.request
import json
import os 
from functools import partial

GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
GPIO.setwarnings(False)
#----------------------------------------rain
GPIO.setup(4,GPIO.IN) 
#--------------------------l298n window
IN1=19
IN2=13
ENA=26
IN3=6
IN4=5
ENB=0

GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)	

pwm1 = GPIO.PWM(ENA,100)
pwm1.start(0)
pwm2 = GPIO.PWM(ENB,100)
pwm2.start(0)
#--------------------------l298n blind
IN5=16	
IN6=20
ENC=21
GPIO.setup(IN5, GPIO.OUT)
GPIO.setup(IN6, GPIO.OUT)
GPIO.setup(ENC, GPIO.OUT)
pwm3 = GPIO.PWM(ENC,100)
pwm3.start(0)
#--------------------------sen030131
pin_to_circuit = 4
#-------------------------SW420
GPIO.setup(2,GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
result = GPIO.input(2)
#-------------------------DHT11
sensor = Adafruit_DHT.DHT11
humidity, temperature = Adafruit_DHT.read_retry(sensor,2)
#-------------------------PMS7003
global pm1,pm2,pm10
# Baud Rate
dust = PMS7003()
Speed = 9600

# UART / USB Serial
USB0 = '/dev/ttyUSB0'
UART = '/dev/ttyAMA0'

# USE PORT
SERIAL_PORT = USB0
 
#serial setting
ser = serial.Serial(USB0,9600, timeout = 1)
#-------------------------firebase
firebase = firebase.FirebaseApplication('https://myapplication-3f8f5.firebaseio.com/', None)
#-------------------------setting with sen030131(light sensor)
def rc_time (pin_to_circuit):
    count = 0
	#----------------------------------setting
    GPIO.setup(pin_to_circuit, GPIO.OUT)
    GPIO.output(pin_to_circuit, GPIO.LOW)
    #Change the pin back to input
    GPIO.setup(pin_to_circuit, GPIO.IN)
	#-----------------------------------
	#-----------------------------------sen030131
    while (GPIO.input(pin_to_circuit) == GPIO.LOW):
        count += 100
    return count
	
def update_firebase():
	while True:
		#SW420 -vibdata
		if result ==1:
			str_vib = 'warning'.format(result)	
			vibdata = {"shock": result}
		firebase.patch('/sensor/vib', vibdata)
		if result ==0:
			str_vib = 'warning'.format(result)	
			vibdata = {"shock": result}
		firebase.patch('/sensor/vib', vibdata)
		#DHT11 -temp
		if humidity is not None and temperature is not None:
			str_temp = ' {0:0.2f} *C '.format(temperature)	
			str_hum  = ' {0:0.2f} %'.format(humidity)
	#print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))	
		tempdata = {"temp": temperature, "humidity": humidity}
		firebase.patch('/sensor/dht', tempdata)
		#PMS7003 - dustdata
		ser.flushInput()
		buffer = ser.read(1024)
		if(dust.protocol_chk(buffer)):
			data = dust.unpack_data(buffer)
	#print("send -PM2.5: %d" %(data[dust.DUST_PM2_5_ATM]))
			pm2=data[dust.DUST_PM2_5_ATM]
		dustdata = {"dust": pm2}
		firebase.patch('/sensor/pms',dustdata)
		#sen030131 - lightdata
		if rc_time(2)< 1800:	
	#print("맑음",rc_time(2))
			lightdata = {"조도값":rc_time(2)}
		if rc_time(2) >=2000:
	#print("흐림",rc_time(2))
			lightdata = {"조도값":rc_time(2)}
		firebase.patch('/sensor/light',lightdata) 	
while True:
		update_firebase()
        #sleepTime = int(sleepTime)
		sleep(1)
#미세먼지+빗물자동제어
while True:
	#firebase 값 가져오기
	#미세먼지 빗물자동제어 버튼 0/01
	result0 = firebase.get('/window','start')
	result01 = firebase.get('/window','nostart')
	#limit setting 
	open= GPIO.input(2)
	close= GPIO.input(3)
	#motor setting
	GPIO.output(IN1, False)
	GPIO.output(IN2, False)
	GPIO.output(IN3, False)
	GPIO.output(IN4, False)
	ser.flushInput()
	buffer = ser.read(1024)
	#자동설정버튼누름
	if result0 =="\"start\"":
		#미세먼지 농도체크
		if(dust.protocol_chk(buffer)):
				data = dust.unpack_data(buffer)
				pm2=data[dust.DUST_PM2_5_ATM]
				#미세먼지 와 빗물감지 여부에따라 모터 작동 # 빗물감지센서는 물의유무보다는 빗물의양에따라 바뀜
				if data[dust.DUST_PM2_5_ATM]<3 or GPIO.input(4)==0:
					print("send -  PM2.5: %d" %data[dust.DUST_PM2_5_ATM])
					pwm1.ChangeDutyCycle(30)
					GPIO.output(IN1, False)
					GPIO.output(IN2, True)
					pwm2.ChangeDutyCycle(30)
					GPIO.output(IN3, False)
					GPIO.output(IN4, True)
				if data[dust.DUST_PM2_5_ATM]>=3	or GPIO.input(4)==1:
					print("send -  PM2.5: %d" %data[dust.DUST_PM2_5_ATM])
					pwm1.ChangeDutyCycle(30)
					GPIO.output(IN1, True)
					GPIO.output(IN2, False)
					pwm2.ChangeDutyCycle(30)
					GPIO.output(IN3, True)
					GPIO.output(IN4, False)
					#limit input-> stop 
					if open == 1 or close ==1:
						GPIO.output(IN1, False)
						GPIO.output(IN2, False)
						GPIO.output(IN1, False)
						GPIO.output(IN2, False)
						print("창문 정지")
	if result01 =="\"nostart\"":
		pwm1.ChangeDutyCycle(30)
		GPIO.output(IN1, True)
		GPIO.output(IN2, False)
		pwm2.ChangeDutyCycle(50)
		GPIO.output(IN3, True)
		GPIO.output(IN4, False)
		#limit input-> stop 
		if close == 1:
			GPIO.output(IN1, False)
			GPIO.output(IN2, False)
			GPIO.output(IN1, False)
			GPIO.output(IN2, False)
			print("창문 정지")
#window수동제어
while True: 
	open= GPIO.input(2) 
	close= GPIO.input(3)
	#window 수동버튼 1/2
	result1 = firebase.get('/window','start') #change 
	result2 = firebase.get('/window','nostart') #change 
	GPIO.output(IN1, False)
	GPIO.output(IN2, False)
	GPIO.output(IN3, False)
	GPIO.output(IN4, False)
	if result1 =="\"start\"": #change 
		pwm1.ChangeDutyCycle(30)
		GPIO.output(IN1, False)
		GPIO.output(IN2, True)
		GPIO.output(IN3, False)
		GPIO.output(IN4, True)
		#limit input-> stop 
		if open == 1 or close ==1:
			GPIO.output(IN1, False)
			GPIO.output(IN2, False)
			GPIO.output(IN1, False)
			GPIO.output(IN2, False)
			print("창문 정지")
	if result2 =="\"nostart\"": #change 
		pwm1.ChangeDutyCycle(30)
		GPIO.output(IN1, True)
		GPIO.output(IN2, False)
		GPIO.output(IN3, True)
		GPIO.output(IN4, False)
		#limit input-> stop 
		if open == 1 or close ==1:
			GPIO.output(IN1, False)
			GPIO.output(IN2, False)
			GPIO.output(IN1, False)
			GPIO.output(IN2, False)
			print("창문 정지")
			
#blind자동제어 
while True:
	#blind 자동버튼 3/4
	result3 = firebase.get('/window','start') #change 
	result4 = firebase.get('/window','nostart') #change 
	#motor setting
	GPIO.output(IN1, False)
	GPIO.output(IN2, False)
	#어플 입력
	if result3=="\"start\"":
		if rc_time(2)< 1800:	
			pwm3.ChangeDutyCycle(30)
			GPIO.output(IN5, False)
			GPIO.output(IN6, True)
			#정지
			time.sleep(3)
			GPIO.output(IN5, False)
			GPIO.output(IN6, False)
		if rc_time(2) >=2000:
			pwm3.ChangeDutyCycle(30)
			GPIO.output(IN5, True)
			GPIO.output(IN6, False)
			#정지
			time.sleep(3)
			GPIO.output(IN5, False)
			GPIO.output(IN6, False)
	#어플 입력
	if result4=="\"nostart\"":
		pwm3.ChangeDutyCycle(30)
		GPIO.output(IN5, False)
		GPIO.output(IN6, True)
		time.sleep(3)
		GPIO.output(IN5, False)
		GPIO.output(IN6, False)
#blind수동제어
while True:
	#blind 수동버튼 7/8
	result7 = firebase.get('/window','start') #change 
	result8 = firebase.get('/window','nostart') #change 
	result9=  firebase.get('/window','stop')#input
	GPIO.output(IN5, False)
	GPIO.output(IN6, False)
	if result1 =="\"start\"": #change 
		pwm3.ChangeDutyCycle(30)
		GPIO.output(IN1, False)
		GPIO.output(IN2, True)
		#blind 정지버튼
		if result9=="\"stop\"":
			GPIO.output(IN6, False)
			GPIO.output(IN5, False)
	if result2 =="\"nostart\"": #change
		pwm3.ChangeDutyCycle(30)
		GPIO.output(IN5,False)
		GPIO.output(IN6,True)
		if result9=="\"stop\"":
			GPIO.output(IN6, False)
			GPIO.output(IN5, False)



