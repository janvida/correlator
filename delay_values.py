#!/usr/bin/python

fout = open('test.txt','w')

for i in range(-2560,2560):
    value = 2560 + i
    delayC = '%0.3x' % (value / 5) #This writes delayC as a three character hex
    delayA = str(value % 5)
    fout.write(str(i)+'\t'+delayC+'\t'+delayA+'\n')

fout.close()
    
#Last edit: Fri Jan 28 2011 00:25
