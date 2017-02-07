#!/usr/bin/python

#Janvida Rou
#Jan 27 2011
#sii_delay.py

import serial
import datetime

filename = 'filename.txt'

start = datetime.datetime.now()
start = start.strftime('%D %H:%M:%S')

ser = serial.Serial('/dev/ttyM1',115200,timeout=1)

null = '\n'

fout = open(filename,'w')

#This section is to clear the buffer before running the delay script
tmp = ser.readline()
if tmp != '':
    tmp = ser.readline()
else:
    pass

#This section is to set the parameters before each run
ser.write('iiec0' + null)
tmp = ser.readline()
ser.write('iigaF'+null) #If this value is changed then the value that checks 
                        #that gainA is set correctly must also be changed
gainA = ser.readline()
if gainA != 'IIGAF\r\n':
    print 'Error IIGA'
else:
    pass
ser.write('iigbF'+null)
gainB = ser.readline()
ser.write('iidaF'+null)
delayA = ser.readline()
ser.write('iidb0'+null)
delayB = ser.readline()
ser.write('iidc200'+null)
coarse_delay = ser.readline()
ser.write('iipa0000'+null)
perA = ser.readline()
ser.write('iipb0000'+null)
perB = ser.readline()

#This section runs through the actual delay script
for i in range(-2560,2560):
    delay = 2560 + i
    delayC = '%0.3x' % (delay / 5) #This writes delayC as a three character hex
    delayA = str(delay % 5) 
    ser.write('iidc' + delayC + null) #Set the coarse delay
    delC = ser.readline()
    delC = delC[4:7] #This is the three character hex that is programmed
    ser.write('iida' + delayA + null) #Set the fine delay
    delA = ser.readline()
    delA = delA[4:5] #This is the value that is programmed as fine delay

#This section captures the accumulator values
    #This is the first run. These values are not used
    ser.write('iiac' + null) #Reset accumulator (first time)
    tmp = ser.readline()
    accum_ready = ser.readline()
    if accum_ready != 'Accumulator Ready\r\n':
        print 'Error IIAC 1'
    else:
        pass
    tmp = ser.readline() #Be sure to clear buffer of messages
    if tmp != '':
        print 'Error: Buffer 1'
    else:
        pass
    ser.write('iiar' + null) #Read accumulator (first time)
    tmp = ser.readline() #Be sure the correct line is read back
    if tmp[:4] != 'IIAR':
        print 'Error reading accumulator 1'
    else:
        pass
    #This is the second run. These values are used
    ser.write('iiac' + null) #Reset accumulator (second time)
    tmp = ser.readline()
    accum_ready = ser.readline()
    if accum_ready != 'Accumulator Ready\r\n':
        print 'Error IIAC 2'
    else:
        pass
    tmp = ser.readline() #Be sure to clear buffer of messages
    if tmp != '':
        print 'Error: Buffer 2'
    else:
        pass
    ser.write('iiar' + null) #Read accumulator (second time)
    val = ser.readline() #Be sure the correct line is read back
    if val[:4] != 'IIAR':
        print 'Error reading accumulator 2'
    else:
        pass

    #Calculation of the accumlator values
    val = val[4:] #Remove IIAR part
    val = int(val,16) #Convert 16 digit hex into dec
    if val > 0x7FFFFFFFFFFFFFFF: #Signed conversion for negatives
        val -= 0x10000000000000000
        value = int(val)
        print str(i) + '\t' + str(delC) + '\t' + str(delA) + '\t' + '%8e' % int(value)
    else: #Signed conversion for positives
        val = val
        value = int(val)
        print str(i) + '\t' + str(delC) + '\t' + str(delA) + '\t' + '%8e' % int(value)
    #The columns of the output file are: 1)User set delay;2)Current coarse delay
    #setting;3)Current fine delay setting;4)Accumulator readout
    fout.write(str(i)+'\t'+str(delC)+'\t'+str(delA)+ '\t' + '%8e' % int(value)+ '\n')


end = datetime.datetime.now()
end = end.strftime('%D %H:%M:%S')

fout.write('\n' + 'Start time: ' + start + '\t' + 'End time: ' + end + '\n')
fout.write('gainA: ' + gainA[:5] + '\n' + 'gainB: ' + gainB[:5] + '\n' + 'perA: ' + perA[:5] + '\n' + 'perB: ' + perB[:5])
print 'end'
print 'File saved to ' + filename

fout.close()

#Last edit: Fri Jan 28 2011 21:40
