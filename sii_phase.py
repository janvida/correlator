import serial
import datetime

start = datetime.datetime.now()
start = start.strftime('%H:%M:%S')

ser=serial.Serial('/dev/ttyM0',115200,timeout=1) #Open serial port

null='\n'

fout = open('record7_2010Nov18-32','w')




#This section is to clear the buffer before running the program
tmp = ser.readline()
if tmp != '':
    tmp = ser.readline()
else: 
    pass

#This section is to set the parameters before each run
ser.write('iiec0' + null)
tmp = ser.readline()
ser.write('iiga0'+null)
gainA = ser.readline()
if gainA != 'IIGA0\r\n':
    print 'Error IIGA'
else:
    pass
ser.write('iigb0'+null)
gainB = ser.readline()
ser.write('iida0'+null)
delayA = ser.readline()
ser.write('iidb0'+null)
delayB = ser.readline()
ser.write('iidc200'+null)
coarse_delay = ser.readline()
ser.write('iipa0000'+null)
tmp = ser.readline()
ser.write('iipb0000'+null)
tmp=ser . readline()

print '\n'

#Set ranges for period of channel A and B
a_range = 32
b_range = 32


for n in range(a_range+1):
    periodA = '%0.4x' % n #Convert n to a 4 digit hex string
    ser.write('iipa' + periodA + null) #Set phase period of channel A
    perA = ser.readline()
    A = perA[4:8]

    for i in range(b_range+1):
        periodB = '%0.4x' % i #Convert i to a 4 digit hex string
        ser.write('iipb' + periodB + null) #Set phase period of channel B
        perB = ser.readline()
        B = perB[4:8]
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
        
        val = val[4:] #Remove IIAR part
        val = int(val,16) #Convert 16 digit hex into dec
        if val > 0x7FFFFFFFFFFFFFFF: #Signed conversion for negatives
            val -= 0x10000000000000000
            value = int(val)
        else: #Signed conversion for positives
            val = val
            value = int(val)
        print 'perA = ' + perA + 'perB = ' + perB + 'c = ' + '%7e' % int(value) + '\n'
        fout.write(str((int(A, 16))).rjust(4) + '  ' + str((int(B, 16))).rjust(4) + '  ' + '%7e' % int(value) + '\n')

end = datetime.datetime.now()
end = end.strftime('%H:%M:%S')
fout.write('\n' + gainA[:5] + ' ' + gainB[:5] + ' ' +  delayA[:5] + ' ' +  delayB[:5] + ' ' +  coarse_delay[:7] + '\n')
fout.write('Start time: ' + start + '\t' + 'End time: ' + end)
            
print 'end'

fout.close()

#Last edit: Fri Jan 28 2011 00:25
