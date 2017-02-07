#!/usr/bin/python

import serial
import datetime

filename = 'r4-delay.txt'

start = datetime.datetime.now()
start = start.strftime('%D %H:%M:%S')

ser = serial.Serial('/dev/ttyM1',115200,timeout=1)

null = '\n'

fout = open(filename,'w')

################################################################################
#This section is to clear the buffer before running the script
################################################################################
tmp = ser.readline()
if tmp != '':
    tmp = ser.readline()
else:
    pass

#################################################################################This section is to set the parameters before running the script
################################################################################
ser.write('iiec0' + null)
echo = ser.readline()
ser.write('iigaF' + null)
gainA = ser.readline()
ser.write('iigbf'+null)
gainB = ser.readline()
ser.write('iida0'+null)
delayA = ser.readline()
ser.write('iidb0'+null)
delayB = ser.readline()
ser.write('iidc200'+null)
coarse_delay = ser.readline()
ser.write('iipa0000'+null)
perA = ser.readline()
ser.write('iipb0000'+null)
perB = ser.readline()

################################################################################
#This section runs through the actual delay script
################################################################################
for i in range(-2560,2560):
    #Defining delay parameters
    delay_shift = 2560 + i #To avoid negatives
    delayC_shift = delay_shift / 5 #Set coarse delay value in intervals of 5ns
    delayC = '%0.3x' % delayC_shift 
    delayA = delay_shift % 5 #Mod of coarse delay to set fine delay
    
    #Writing commands to board
    ser.write('iidc' + delayC + null)
    delC = ser.readline()[4:7] #Reads the hex value of the set coarse delay
    ser.write('iida' + str(delayA) + null)
    delA = ser.readline()[4:5] #Reads the value of the set fine delay

    #Capturing accumulator value. First run, values are discarded.
    ser.write('iiac' + null) #Reset accumulator
    tmp = ser.readline()
    accum_ready = ser.readline()
    if accum_ready != 'Accumulator Ready\r\n':
        print 'Error IIAC 1'
    else:
        pass
    tmp = ser.readline() #Be sure to clear buffer of messages
#    if tmp != '':
#        print 'Error: Buffer 2'
        #tmp = ser.readline()
#    else:
#        pass
    ser.write('iiar' + null) #Read a value from the accumulator
    accum_chk = ser.readline()
    if accum_chk[:4] != 'IIAR':
        print 'Error reading accumulator value 1'
    else:
        pass

    #Capturing accumulator value. Second run, values are recorded
    ser.write('iiac' + null) #Reset accumulator
    tmp = ser.readline()
    accum_ready = ser.readline()
    if accum_ready != 'Accumulator Ready\r\n':
        print 'Error IIAC 2'
    else:
        pass
    tmp = ser.readline() #Be sure to clear buffer of messages
    if tmp != '':
        print 'Error: Buffer 2'
        #tmp = ser.readline()
    else:
        pass
    ser.write('iiar' + null) #Read a value from the accumulator
    val = ser.readline()
    if val[:4] != 'IIAR':
        print 'Error reading accumulator value 2'
    else:
        pass

    #Calculate decimal accumulator readout
    val = val[4:] #Remove IIAR
    val = int(val,16) #Convert 16 digit hex to int
    if val > 0x7FFFFFFFFFFFFFFF: #Signed conversion for negatives
        val -= 0x10000000000000000
        value = int(val)
        print str(i) + '\t' + str(delC) + '\t' + str(delA) + '\t' + '%8e' % int(value)
    else: #Signed conversion for positives
        val = val
        value = int(val)
        print str(i) + '\t' + str(delC) + '\t' + str(delA) + '\t' + '%8e' % int(value)

    #Write out values to file
    #The columns of the output file are: 1)User set delay;2)Current coarse delay
    #setting;3)Current fine delay setting;4)Accumulator readout
    fout.write(str(i) + '\t' + str(delC) + '\t' + str(delA)+ '\t' + '%8e' % int(value) + '\n')

################################################################################
#Record parameters to file
################################################################################

end = datetime.datetime.now()
end = end.strftime('%D %H:%M:%S')

fout.write('\n' + 'Start time: ' + start + '\t' + 'End time: ' + end + '\n')
fout.write('gainA: ' + gainA[:5] + '\n' + 'gainB: ' + gainB[:5] + '\n' + 'perA: ' + perA[:5] + '\n' + 'perB: ' + perB[:5])
print 'end'
print 'File saved to ' + filename

fout.close()
