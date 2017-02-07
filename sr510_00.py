#!/usr/bin/python2.6
import serial
import decimal
import time
import datetime
#Define default serialcom settings
BAUD='19200'
Port1='/dev/ttyUSB0'
ser = serial.Serial(Port1, BAUD, timeout=1) 

for n in range(0,5,1):
 ser.write("X1\r")
 x1=ser.readline()
# print(str(x1))
 ser.write("X2\r")
 x2= ser.readline()
# print str(x2)
 ser.write("q\r")
 q= ser.readline()
 now = datetime.datetime.now()

 print n, now, decimal.Decimal(x1), decimal.Decimal(x2), decimal.Decimal(q)
 #now=now.strftime("%H:%M:%S")

