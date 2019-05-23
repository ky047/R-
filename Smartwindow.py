import RPi.GPIO as GPIO
import time
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
GPIO.setwarnings(False)
#----------------------------------------rain
GPIO.setup(14,GPIO.IN) 
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
#-------------------------DHT11
sensor = Adafruit_DHT.DHT11
humidity, temperature = Adafruit_DHT.read_retry(sensor,3)
#-------------------------PMS7003
global pm2
# Baud Rate
dust = PMS7003()
Speed = 9600

# UART / USB Serial
USB0 = '/dev/ttyUSB0'
UART = '/dev/ttyAMA0'

# USE PORT
SERIAL_PORT = USB0
 
#serial setting
ser = serial.Serial(USB0,Speed, timeout = 1)
#-------------------------firebase
firebase = firebase.FirebaseApplication("https://window-6216a.firebaseio.com/", None))
#센서값 새로고침
F5=firebase.get('/새로고침,수동제어','F5') 
#진동값 1에서0으로 새로고침
#-------------------------setting with sen030131(light sensor)
#------------------------변수+인터럽트
#--------------------------limit
GPIO.setup(21,GPIO.IN) #pull_up_down=GPIO.PUD_UP)
GPIO.setup(20,GPIO.IN)
status=0
a=1
b=1
c=1
d=1
def my_callback(channel):
	global status,a,b,c
	if status==0:
		status=1
		a=0
		c=0
		#if b==1: 
		#	c=0
def my_callback1(channel):
	global status,b
	if status ==0:
		status=1
		b=0
		d=0
GPIO.add_event_detect(21,GPIO.RISING,callback=my_callback)
GPIO.add_event_detect(20,GPIO.RISING,callback=my_callback1)
control=firebase.get('/새로고참,수동제어','창문제어클릭') #수동제어
control2=firebase.get('/AUTO','AUTO')   #자동제어 #수정
#firebase에 업로드되는값이 많을수록 느리다
#window수동제어
if control== "\"1\"": 
		print("수동제어온")	
		windowsetup=firebase.get('/새로고침,수동제어'/windowcontrol,'state') #창문수동제어 - 버튼(left/right) 
		if a==1:
			if windowsetup =="\"left\"":
				pwm1.ChangeDutyCycle(30)
				GPIO.output(IN1,GPIO.LOW)
				GPIO.output(IN2,GPIO.HIGH)
				pwm2.ChangeDutyCycle(30)
				GPIO.output(IN3,GPIO.LOW)
				GPIO.output(IN4,GPIO.HIGH)
				print("수동제어열고있는중")	
		if a==0:
			print("수동제어정지1")	
			GPIO.output(IN1,GPIO.LOW)
			GPIO.output(IN2,GPIO.LOW)
			GPIO.output(IN3,GPIO.LOW)
			GPIO.output(IN4,GPIO.LOW)
		if b==1:
			if windowsetup1 =="\"right\"":
				a=1
				pwm1.ChangeDutyCycle(30)
				GPIO.output(IN1,GPIO.HIGH)
				GPIO.output(IN2,GPIO.LOW)
				pwm2.ChangeDutyCycle(30)
				GPIO.output(IN3,GPIO.HIGH)
				GPIO.output(IN4,GPIO.LOW)
				status=0
				print("수동제어닫고있는중")	
		if b==0:
			print("수동제어정지2")	
			GPIO.output(IN1,GPIO.LOW)
			GPIO.output(IN2,GPIO.LOW)
			GPIO.output(IN3,GPIO.LOW)
			GPIO.output(IN4,GPIO.LOW)
			status=0
			c=1
			d=1
#window 자동제어
if control2== "\"AUTO\"": #수정
		print("자동제어온")	
		result1 = firebase.get('/AUTO','START') #수정
		result2 = firebase.get('/AUTO','STOP')  #수정
		ser.flushInput()
		buffer = ser.read(1024)
		if result1 =="\"START\"":
			if c==1:
				if(dust.protocol_chk(buffer)):
					data = dust.unpack_data(buffer)
					pm2=data[dust.DUST_PM2_5_ATM]
					if data[dust.DUST_PM2_5_ATM]<3:
						print("자동제어열고있는중")	
						print("send -  PM2.5: %d" %data[dust.DUST_PM2_5_ATM])
						pwm1.ChangeDutyCycle(30)
						GPIO.output(IN1, )
						GPIO.output(IN2, GPIO.HIGH)
						pwm2.ChangeDutyCycle(30)
						GPIO.output(IN3, GPIO.LOW)
						GPIO.output(IN4, GPIO.HIGH)
					if data[dust.DUST_PM2_5_ATM]>=3:	
						print("send -  PM2.5: %d" %data[dust.DUST_PM2_5_ATM])
						print("자동제어닫고있는중")	
						pwm1.ChangeDutyCycle(30)
						GPIO.output(IN1, GPIO.HIGH)
						GPIO.output(IN2, GPIO.LOW)
						pwm2.ChangeDutyCycle(30)
						GPIO.output(IN3, GPIO.HIGH)
						GPIO.output(IN4, GPIO.LOW)
			if c==0 or d==0:
				print("자동제어정지")#1
				GPIO.output(IN1, GPIO.LOW)
				GPIO.output(IN2, GPIO.LOW)
				GPIO.output(IN3, GPIO.LOW)
				GPIO.output(IN4, GPIO.LOW)
		if result2 =="\"STOP\"": #수정
			if d==1:
				print("자동제어 원상복구")#1
				pwm1.ChangeDutyCycle(30)
				GPIO.output(IN1, GPIO.HIGH)
				GPIO.output(IN2, GPIO.LOW)
				pwm2.ChangeDutyCycle(50)
				GPIO.output(IN3, GPIO.HIGH)
				GPIO.output(IN4, GPIO.LOW)
			if d==0:
				print("자동제어 정지!!")#1
				GPIO.output(IN1,GPIO.LOW)
				GPIO.output(IN2, GPIO.LOW)
				GPIO.output(IN3, GPIO.LOW)
				GPIO.output(IN4, GPIO.LOW)	
def update_firebase():
	while True:
		#DHT11 -temp
		if humidity is not None and temperature is not None:
			str_temp = ' {0:0.2f} *C '.format(temperature)	
			str_hum  = ' {0:0.2f} %'.format(humidity)
			print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))	
		tempdata = {"temp": temperature, "humidity": humidity}
		firebase.patch('/sensor/dht', tempdata)
		#PMS7003 - dustdata	
		ser.flushInput()
		buffer = ser.read(1024)
		if (dust.protocol_chk(buffer)):
			data = dust.unpack_data(buffer)
			print("send -| PM2.5: %d "%(data[dust.DUST_PM2_5_ATM]))
			pm2=data[dust.DUST_PM2_5_ATM]
		pm2=data[dust.DUST_PM2_5_ATM]
		dustdata = {"dust": pm2}
		firebase.patch('/sensor/pms',dustdata)
while True:
	#새로고침 버튼
	if F5=="\"1\"":
		update_firebase()
	check=firebase.get('/sensor','vibreset')
	#SW420 센서
	result = GPIO.input(2)
	if result==1:
		str_vib = 'warning'.format(result)	
		print('shock'.format(result))	
		datad={"shock":result}
		firebase.patch('/sensor/vib',datad)
	#SW420 초기화
	if check =="\"1\"":
		resultd=0
		dataa={"shock":resultd}
		firebase.patch('/sensor/vib',dataa)
	if blinde상태== "\"1\"":
  		 firebase.patch('/setup',/블라인드상태)
#미세먼지+빗물자동제어
"""
while True:
	#firebase 값 가져오기
	#미세먼지 빗물자동제어 버튼 0/01
#	result0 = firebase.get('/window','start')
#	result01 = firebase.get('/window','nostart')
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
"""
#limit -> 2핀/3핀 고정

#blind자동제어 
"""
while result3=="\"start\"": #change
	#blind 자동버튼 3/4
	#result3 = firebase.get('/window','start') #change 
	#result4 = firebase.get('/window','nostart') #change 
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
	#result7 = firebase.get('/window','start') #change 
	#result8 = firebase.get('/window','nostart') #change 
	#result9=  firebase.get('/window','stop')#input
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
"""


