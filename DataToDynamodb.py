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

# Number of Sensor to connect (Max 8)
numberOfSensors = 6
tool = [None]*numberOfSensors

# Tempretrue base line
baseline = 250;

# Iteration counter
iter = 0


ACCOUNT_ID = ''
IDENTITY_POOL_ID = ''
ROLE_ARN = ''

# Use cognito to get an identity.
cognito = boto.connect_cognito_identity()
cognito_id = cognito.get_id(ACCOUNT_ID, IDENTITY_POOL_ID)
oidc = cognito.get_open_id_token(cognito_id['IdentityId'])

# Further setup your STS using the code below
sts = boto.connect_sts()
assumedRoleObject = sts.assume_role_with_web_identity(ROLE_ARN, "XX", oidc['Token'])
DYNAMODB_TABLE_NAME = ''
TableName= ''

# Prepare DynamoDB client
client_dynamo = boto.dynamodb2.connect_to_region(
    'us-east-1',
    aws_access_key_id=assumedRoleObject.credentials.access_key,
    aws_secret_access_key=assumedRoleObject.credentials.secret_key,
    security_token=assumedRoleObject.credentials.session_token)

# Create table or write to exist table
try:
    table = Table.create(TableName, schema=[HashKey('Sensor')], connection=client_dynamo)
except boto.exception.JSONResponseError:
    table=Table(TableName, connection=client_dynamo)

# Convert hex from reading data
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

        # Calibration for 20 seconds
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
                	time.sleep(1)

                    # Request data
                	tool[i].sendline('char-write-req 0x2b 0x01')
                	tool[i].expect('Notification handle = 0x002a value: 0b .*')
                	
                    # Decode data
                    rval = tool[i].after.split()

                	accX = int(floatfromhex(str(rval[7]) + str(rval[6])))
                	accY = int(floatfromhex(str(rval[9]) + str(rval[8])))
                	accZ = int(floatfromhex(str(rval[11]) + str(rval[10])))

	                gyrX = int(floatfromhex(str(rval[13]) + str(rval[12])))
        	        gyrY = int(floatfromhex(str(rval[15]) + str(rval[14])))
                	gyrZ = int(floatfromhex(str(rval[17]) + str(rval[16])))

	                magX = int(floatfromhex(str(rval[19]) + str(rval[18])))
        	        magY = int(floatfromhex(str(rval[21]) + str(rval[20])))
                	magZ = int(floatfromhex(str(rval[23]) + str(rval[22])))

                    # Request data
                    tool[i].expect('Notification handle = 0x002a value: 34 .*')

                    # Decode data    
                    rval2 = tool[i].after.split()
                    hum  = int(floatfromhex(str(rval2[7]) + str(rval2[6])))
                    temp  = int(round(floatfromhex(str(rval2[11]) + str(rval2[10])) / 10 , 3)*10)
                    timestamp = datetime.fromtimestamp(time.time()-4*60*60).strftime('%Y-%m-%d %H:%M:%S')
                    currentTemp = temp
                    tempArray[storeTo + i*past] = temp

                	if tempArray[past*numberOfSensors - 1] != 0:
		    		    averageTemp = numpy.mean(tempArray[0+i*past : 19+i*past])
                        print "average: " + str(averageTemp)
				        print "current: " + str(temp)
			    	if (currentTemp > averageTemp + 1) or ((currentTemp > baseline + 30) and (currentTemp > averageTemp)) or (currentTemp > baseline + 80):
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
                        Occupancy = "empty"
                    if (OccupancyTemp == "occupied") and (OccupancyAccZ == "occupied"):
                        Occupancy = "occupied"
                    if ((OccupancyTemp == "empty") and (OccupancyAccZ == "occupied")) or ((OccupancyTemp == "occupied") and (OccupancyAccZ == "empty")):
                        Occupancy = "uncertain"

			if (i == 0):
				iter = iter + 1



			print "Putting data to db"
			print str(i)
			print str(iter)
			print Occupancy
			
            # Update data in dynamodb
			update = table.get_item(Sensor = str(i))
			update['Timestamp'] = timestamp
			update['Iter'] = str(iter)
			update['StatusT'] = OccupancyTemp
			update['StatusA'] = OccupancyAccZ
			update['Status'] = Occupancy
			update['accX'] = accX
			update['accY'] = accY
			update['accZ'] = accZ
			update['gyrX'] = gyrX
			update['gyrY'] = gyrY
			update['gyrZ'] = gyrZ
			update['magX'] = magX
			update['magY'] = magY
			update['magZ'] = magZ
			update['Temp'] = temp
			update['Hum'] = hum
			update.save(overwrite=True)

            # Initialize table (Only run for first time)
#			table.put_item(data={
#					'Sensor': str(i),
#					'Timestamp': timestamp,
#					'Iter': str(iter),
#					'StatusT': OccupancyTemp,
#					'StatusA': OccupancyAccZ,
#					'Status': Occupancy,
#					'accX': accX,
#					'accY': accY,
#					'accZ': accZ,
#					'gyrX': gyrX,
#					'gyrY': gyrY,
#		                        'gyrZ': gyrZ,
#	               		        'magX': magX,
#		                        'magY': magY,
#                		        'magZ': magZ,
#  	             		        'Temp': temp,
#					'Hum': hum})

                except pexpect.TIMEOUT:
                        print "Stopped collecting"
                        break
			
		except KeyboardInterrupt:
            		for i in range(0, numberOfSensors):
	        		tool[i].sendline('disconnect ' + sys.argv[i+1])
                		print "disonnect from " + str(i) + " successfully"
            		break  
