import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import csv
import pexpect
import sys
import time
import csv
import threading
import numpy
import decimal
import boto.dynamodb2
from boto.dynamodb2.fields import HashKey, RangeKey, KeysOnlyIndex, GlobalAllIndex
from boto.dynamodb2.table import Table
from boto.dynamodb2.types import NUMBER
from datetime import datetime

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
DYNAMODB_TABLE_NAME = 'edisonDemoDynamo'
TableName= 'SmartSeats'

# Prepare DynamoDB client
client_dynamo = boto.dynamodb2.connect_to_region(
    'us-east-1',
    aws_access_key_id=assumedRoleObject.credentials.access_key,
    aws_secret_access_key=assumedRoleObject.credentials.secret_key,
    security_token=assumedRoleObject.credentials.session_token)

try:
    table = Table.create(TableName, schema=[HashKey('Sensor')], connection=client_dynamo)
except boto.exception.JSONResponseError:
    table=Table(TableName, connection=client_dynamo)

#x = []
y = []
iter = 0
while True:
        for row in range(0, 3):
                data = table.get_item(Sensor = str(row))
                print data['Iter']
                print data['accX']
#                x.append(data['Iter'])
                y.append(data['accX'])
	iter = iter + 1
        plt.plot(iter, y[0], 'r--', iter, y[1], 'bs', iter, y[2], 'g^')
        plt.pause(0.2)	

