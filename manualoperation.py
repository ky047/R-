import RPi.GPIO as GPIO
import time 
import datetime
from firebase import firebase

import urllib.request
import json
import os 
from functools import partial
#firebase = firebase.FirebaseApplication("https://window-6216a.firebaseio.com/", None)
firebase = firebase.FirebaseApplication("https://myapplication-3f8f5.firebaseio.com/", None)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#----------------------------------------limit 
GPIO.setup(21, GPIO.IN) #pull_up_down=GPIO.PUD_UP)
#GPIO.add_event_detect(2, GPIO.RISING)
IN1=19
IN2=13
ENA=26

GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)
#GPIO.setup(IN3, GPIO.OUT)
#GPIO.setup(IN4, GPIO.OUT)
#GPIO.setup(ENB, GPIO.OUT)	
pwm1 = GPIO.PWM(ENA, 50)
pwm1.start(0)

#control= firebase.get('/test3','control')	
control=firebase.get('/window','open')
#pwm2 = GPIO.PWM(ENB,50)
#pwm2.start(50)
#------------변수 
status=0
a=1
def my_callback(channel):
	global status,a
	if status==0:
		print("on")
		a=0
		status=1
GPIO.add_event_detect(21,GPIO.RISING,callback=my_callback)
while control== "\"open\"":
	#windowsetup=firebase.get('/test3/windowcontrol','state')
	windowsetup=firebase.get('/window','start')
	GPIO.output(IN1, False)
	GPIO.output(IN2, False)
	if windowsetup =="\"start\"":
		pwm1.ChangeDutyCycle(30)
		GPIO.output(IN1, False)
		GPIO.output(IN2, True)
		if a==0:
			GPIO.output(IN1, False)
			GPIO.output(IN2, False)
		#GPIO.add_event_detect(21,GPIO.RISING,callback=my_callback)
		#if open == 1: #or close ==1:
			#GPIO.add_event_detect(21,GPIO.RISING,callback=my_callback)
	windowsetup1=firebase.get('/window','nostart')
	if windowsetup1 =="\"nostart\"":
		pwm1.ChangeDutyCycle(30)
		GPIO.output(IN1, True)
		GPIO.output(IN2, False)
		if a==0:
			GPIO.output(IN1, False)
			GPIO.output(IN2, False)
