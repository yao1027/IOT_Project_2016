import pexpect
import sys
import time
import csv
import threading
import numpy
import decimal
import boto3
import botocore.session
import boto.dynamodb2
from boto3.dynamodb.conditions import Key, Attr
from boto.dynamodb2.fields import HashKey, RangeKey, KeysOnlyIndex, GlobalAllIndex
from boto.dynamodb2.table import Table
from boto.dynamodb2.types import NUMBER
from datetime import datetime

numberOfSensors = 3
tool = [None]*numberOfSensors
baseline = 25;
iter = 0

# export PATH=$PATH:~/bluez-5.24/attrib/


def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
        pass
    return t

if __name__ == "__main__":
    while 1:
	for i in range(0, numberOfSensors):
	        bluetooth_adr = sys.argv[i+1]
        	tool[i] = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
        	tool[i].expect('\[LE\]>')
        	print "Preparing to connect to " + str(i)
        	tool[i].sendline('connect')
        	tool[i].expect('Connection successful')
        	print "Connection to " + str(i) + " successful"

	f = open("data7.csv", "wb")
    	file = csv.writer(f,delimiter = ',')
    	header = ['Sensor', 'Occupancy', 'OccupancyTemp', 'OccupancyAccZ', 'Iteration', 'TimeStamp', 'accX', 'accY', 'accZ', 'gyrX', 'gyrY', 'gyrZ', 'magX', 'magY', 'magZ', 'Temp']
    	file.writerow(header)

	if (iter == 0):

	    	past = 20
		tempArray = []
	    	for i in range(past*numberOfSensors):
			tempArray.append(0)

		storeTo = 0
		storeToAccZ = 0

		OccupancyTemp = "calibrating"
		OccupancyAccZ = "calibrating"

	    	accZArray = []
    		for i in range(past*numberOfSensors):
        		accZArray.append(0)

	while True:
		try:
        	    for i in range(0, numberOfSensors):
                	time.sleep(2)
                	tool[i].sendline('char-write-req 0x2b 0x01')
                	tool[i].expect('Notification handle = 0x002a value: 0b .*')
                	rval = tool[i].after.split()

                	accX = floatfromhex(str(rval[7]) + str(rval[6]))
                	accY = floatfromhex(str(rval[9]) + str(rval[8]))
                	accZ = floatfromhex(str(rval[11]) + str(rval[10]))

	                gyrX = floatfromhex(str(rval[13]) + str(rval[12]))
        	        gyrY = floatfromhex(str(rval[15]) + str(rval[14]))
                	gyrZ = floatfromhex(str(rval[17]) + str(rval[16]))

	                magX = floatfromhex(str(rval[19]) + str(rval[18]))
        	        magY = floatfromhex(str(rval[21]) + str(rval[20]))
                	magZ = floatfromhex(str(rval[23]) + str(rval[22]))

			tool[i].expect('Notification handle = 0x002a value: 34 .*')
			rval2 = tool[i].after.split()
			hum  = floatfromhex(str(rval2[7]) + str(rval2[6]))
			temp  = round(floatfromhex(str(rval2[11]) + str(rval2[10])) / 10 , 3)
			timestamp = datetime.fromtimestamp(time.time()-4*60*60).strftime('%Y-%m-%d %H:%M:%S')
			currentTemp = temp
			tempArray[storeTo + i*past] = temp

                	if tempArray[past*numberOfSensors - 1] != 0:
		    		averageTemp = numpy.mean(tempArray[0+i*past : 19+i*past])
				print "average: " + str(averageTemp)
				print "current: " + str(temp)
			    	if (currentTemp > averageTemp + 0.1) or ((currentTemp > baseline + 3) and (currentTemp > averageTemp)) or (currentTemp > baseline + 8):
					print str(i) + "temp: occupied"
			    		OccupancyTemp = "occupied"
		    		else:
					print str(i) + "temp: empty"
		    			OccupancyTemp = "empty"

			currentAccZ = accZ

                        if (storeToAccZ < past):
                                accZArray[storeToAccZ + i*past] = accZ

                        if accZArray[past*numberOfSensors - 1] != 0:
                                averageAccZ = numpy.mean(accZArray[0+i*past : 19+i*past])
                                print "average accZ: " + str(averageAccZ)
                                print "accZ: " + str(accZ)

                                if (currentAccZ > averageAccZ + 3) or (currentAccZ < averageAccZ - 3):
                                        print "accZ: occupied"
                                        OccupancyAccZ = "occupied"
                                else:
                                     	print "accZ: empty"
                                        OccupancyAccZ = "empty"

                        if (i == numberOfSensors - 1):
                                storeTo = storeTo + 1
                                storeToAccZ = storeToAccZ + 1

                        if (storeTo == past):
                                storeTo = 0

                        if (storeToAccZ >= past):
                                storeToAccZ = past

                        if (OccupancyTemp == "calibrating") and (OccupancyAccZ == "calibrating"):
                                Occupancy = "calibrating"
                        if (OccupancyTemp == "empty") and (OccupancyAccZ == "empty"):
                                Occupancy = "0"
                        if (OccupancyTemp == "occupied") and (OccupancyAccZ == "occupied"):
                                Occupancy = "1"
                        if ((OccupancyTemp == "empty") and (OccupancyAccZ == "occupied")) or ((OccupancyTemp == "occupied") and (OccupancyAccZ == "empty")):
                                Occupancy = "2"

			if (i == 0):
				iter = iter + 1

			print "Putting data to csv"
			print str(i)
			print str(iter)
			print Occupancy
			file.writerow([str(i), Occupancy, OccupancyTemp, OccupancyAccZ, iter, timestamp, accX, accY, accZ, gyrX, gyrY, gyrZ, magX, magY, magZ, str(temp)])

                except pexpect.TIMEOUT:
                        print "Stopped collecting"
                        break
			
		except KeyboardInterrupt:
            		for i in range(0, numberOfSensors):
	        		tool[i].sendline('disconnect ' + sys.argv[i+1])
                		print "disonnect from " + str(i) + " successfully"
            		break  
