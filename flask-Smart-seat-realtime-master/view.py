import os, datetime,time
import psycopg2
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, session, render_template, g, redirect, Response, flash, url_for
from boto.dynamodb2.fields import HashKey
from boto.dynamodb2.table import Table
import boto3
import time
from flask import Flask
from flask.ext.dynamo import Dynamo


ACCOUNT_ID = '181655739680'
IDENTITY_POOL_ID = 'us-east-1:382173b3-57d3-4d56-babd-0e0106c96f88'
ROLE_ARN = 'arn:aws:iam::181655739680:role/Cognito_edisonDemoKinesisUnauth_Role'
COGNITO_ID = "EdisonApp"
region = 'us-east-1'

def init_db():
    client_dynamo = getClient ('dynamodb', region)
    dynamodb = getResource('dynamodb',region)
    table=dynamodb.Table('SmartSeats')
    return table


def getCredentials():

    cognito = boto3.client('cognito-identity','us-east-1')
    cognito_id = cognito.get_id(AccountId=ACCOUNT_ID, IdentityPoolId=IDENTITY_POOL_ID)
    oidc = cognito.get_open_id_token(IdentityId=cognito_id['IdentityId'])

    sts = boto3.client('sts')
    assumedRoleObject = sts.assume_role_with_web_identity(RoleArn=ROLE_ARN,\
                                                          RoleSessionName=COGNITO_ID,\
                                                          WebIdentityToken=oidc['Token'])

    credentials = assumedRoleObject['Credentials']
    return credentials

def getResource(resourceName,region):
    credentials = getCredentials()
    resource = boto3.resource(resourceName,
                              region,
                              aws_access_key_id= credentials['AccessKeyId'],
                              aws_secret_access_key=credentials['SecretAccessKey'],
                              aws_session_token=credentials['SessionToken'])
    return resource

def getClient(clientName,region):
    credentials = getCredentials()
    client = boto3.client(clientName,
                          region,
                          aws_access_key_id= credentials['AccessKeyId'],
                          aws_secret_access_key=credentials['SecretAccessKey'],
                          aws_session_token=credentials['SessionToken'])
    return client


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


app.config.update(dict(
    SECRET_KEY='development key',
))
#DATABASEURI = "sqlite:///test.db"
DATABASEURI = "postgresql://kesin:123@bigdatabase.eastus.cloudapp.azure.com/testdb"

engine = create_engine(DATABASEURI)


@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
    print ('Connected to my database!')
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
    print ('Disconnected from my database!')
  except Exception as e:
    pass

@app.route('/view',methods = ['GET', 'POST'])
def view():
                table = init_db()
                item = []
                infor = table.scan()
                information = list(infor['Items'])
                return render_template('view.html', information = information)
                print 'ouch'


@app.route('/', methods=['GET','POST'])
def index():
        print request.args
        sid_tmp = session.get('s_id')
        print sid_tmp
        if sid_tmp is not None and session['logged_in'] is not None:

                if request.method == 'POST':
                        cursor= g.conn.execute("SELECT * FROM seat order by seat_id;")

                        seats = cursor.fetchall()
                        seatid_list = []
                        time_list =[]
                        available_list =[]

                        for seat in seats:
                                seatid_list.append(seat['seat_id'])
                                time_list.append(seat['time_period'])
                                available_list.append(seat['available'])
                        if request.form.get("subject", None) == "Show all Seats":
                                return render_template('index.html', s_id = str(session['s_id']), seats = seats)
                        elif request.form.get("subject", None) == "Make a reservation":
                                make_reservation = True
                                return render_template('index.html', make_reservation = make_reservation)

                        elif request.form.get("subject", None) == "Show all you reserved":
                                print session['s_id']

                                cursor = g.conn.execute("select * from reserved where s_id = (%s) order by seat_id;", str(session.get('s_id')))
                                self_reserved = cursor.fetchall()
                                return render_template('index.html', s_id = str(session['s_id']), self_reserved = self_reserved)

                        elif request.form.get("subject", None) == "Cancel your reservation":
                                delete = True
                                cursor = g.conn.execute("select * from reserved where s_id = (%s);", str(session['s_id']))
                                sreserved = cursor.fetchall()

                                return render_template('index.html', s_id = str(session.get('s_id')), delete = delete, sreserved= sreserved)

                        elif request.form.get("subject2", None) == "cancel":
                                print session['s_id']
                                cursor = g.conn.execute("select * from reserved where s_id = (%s);", str(session['s_id']))
                                sreserved = cursor.fetchall()
                                sreserved_timelist = []
                                sreserved_seat = []
                                delete = True
                                for sre in sreserved:
                                        sreserved_timelist.append(sre.time_period)
                                        sreserved_seat.append(sre.seat_id)

                                for i in range(0, len(sreserved_timelist)):
                                        if str(sreserved_seat[i]) == str(request.form.get("cancelseat", None)):
                                                if str(request.form.get('time_period', None)) == str(sreserved_timelist[i]):
                                                        p = "delete from reserved"\
                                                        " where s_id = (%s) and time_period = (%s);"
                                                        values = (str(session['s_id']), request.form['time_period'])
                                                        g.conn.execute(p, values)
                                                        p = "update seat set available = 'yes'"\
                                                        " where seat_id = (%s) and time_period = (%s);"
                                                        values = (str(sreserved_seat[i]),str(sreserved_timelist[i]))
                                                        g.conn.execute(p,values)

                                                        cursor = g.conn.execute("select * from reserved where s_id = (%s);", str(session['s_id']))
                                                        sreserved = cursor.fetchall()
                                                        return render_template('index.html', s_id = str(session.get('s_id')), delete = delete, sreserved= sreserved)
                                                else:
                                                        seat_notice = 'Invalid request. Please select another time_period.'
                                                        return render_template('index.html', s_id = str(session.get('s_id')), sreserved= sreserved,delete = delete, seat_notice = seat_notice)  
                                        else:
                                                seat_notice = 'Invalid seat_id. Please enter another SEAT_ID.'
                                                return render_template('index.html', s_id = str(session.get('s_id')), seat_notice = seat_notice, sreserved= sreserved, delete = delete)
                                return render_template('index.html', s_id = str(session.get('s_id')), sreserved= sreserved, delete = delete)

                        elif request.form.get("subject2", None) == "reserve":
                                seatid_chose = request.form.get("object", None)
                                time_chose = request.form.get("time_period1", None)
                                seat_notice = ''
                                reserved_success = False
                                reserved_confirm = True
                                print 'shit'
                                cursor = g.conn.execute("SELECT * FROM reserved;")
                                reserveds = cursor.fetchall()
                                rsid_list = []
                                rseatid_list = []
                                rtime_list = []
                                for reserved in reserveds:
                                        rsid_list.append(reserved['s_id'])
                                        rseatid_list.append(reserved['seat_id'])
                                        rtime_list.append(reserved['time_period'])
                                for i in range(0,len(rtime_list)):
                                        if str(time_chose) == str(rtime_list[i]):
                                                if str(seatid_chose) == str(rseatid_list[i]):
                                                        seat_notice = 'The seat has been reserved in this time period.'
                                                        return render_template('index.html',reserved_confirm = reserved_confirm, s_id = str(session['s_id']),seat_notice = seat_noti$
                                                elif str(session['s_id']) == str(rsid_list[i]):
                                                        seat_notice = 'You should not reserve two seats in the same time.'
                                                        return render_template('index.html', s_id = str(session['s_id']), reserved_confirm = reserved_confirm,seat_notice = seat_not$
                                                elif str(seatid_chose) == '':
                                                        seat_notice = 'Please select a seat.'
                                                        return render_template('index.html',reserved_confirm = reserved_confirm, s_id = str(session['s_id']),seat_notice = seat_noti$
                                                else:
                                                        reserved_success = True
                                        elif str(time_chose) == '':
                                                seat_notice = 'Please select a time period.'
                                                return render_template('index.html', s_id = str(session['s_id']), reserved_confirm = reserved_confirm,seat_notice = seat_notice)
                                        else:
                                                reserved_success = True

                                if reserved_success == True:
                                        if str(time_chose) == 'None':
                                                seat_notice = 'Please select a time period.'
                                                return render_template('index.html', s_id = str(session['s_id']), reserved_confirm = reserved_confirm,seat_notice = seat_notice)
                                        else:
                                                p = "Insert into reserved values(%s, %s ,%s);"
                                                values = (str(session['s_id']), str(seatid_chose), str(time_chose))
                                                g.conn.execute(p, values)

                                                for i in range(0,len(seatid_list)):
                                                    if str(seatid_chose) == str(seatid_list[i]) and str(time_chose) == str(time_list[i]):
                                                        if str(available_list[i]) == "yes":
                                                                seat_notice = 'You have successfully reserved seat' + seatid_list[i] +' from ' + time_list[i] +'.'
                                                                p = "update seat set available ='no'"\
                                                                " where seat_id = (%s) and time_period =(%s);"
                                                                value = (str(seatid_chose),str(time_chose))
                                                                g.conn.execute(p,value)
                                                                return render_template('index.html', s_id = str(session['s_id']), seat_notice = seat_notice,reserved_confirm = reser$
                                                        elif available_list[i] == 'no':
                                                                seat_notice = 'This seat have already been reserved!\n Please select another seat.'
                                                                return render_template('index.html', s_id = str(session['s_id']), seat_notice = seat_notice,reserved_confirm = reser$
                                return render_template('index.html', s_id = str(session['s_id']),reserved_confirm = reserved_confirm)
        return render_template("index.html")

@app.route('/login',methods=['GET','POST'])
def login():
        error = None
        cursor = g.conn.execute("SELECT * FROM student;")
        sid_list=[]
        password_list=[]
        i = 1
        for result in cursor:
                sid_list.append(result['s_id'])
                password_list.append(result['password'])
        cursor.close
        if request.method == 'POST':
                for i in range(0, len(sid_list)):
                        if str(request.form['s_id']) == str(sid_list[i]):
                                if str(request.form['password']) == str(password_list[i]):


                                        session['logged_in'] = True
                                        session['s_id'] = sid_list[i]
                                        print session['s_id']
                                        return redirect(url_for('index'))
                        error = 'Invalid sid or password'
        return render_template("login.html", error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
        error = None
        cursor = g.conn.execute("SELECT * FROM student;")
        sid_list = []
        for result in cursor:
                sid_list.append(result.s_id)
        cursor.close
        print sid_list[0]
        if request.method == 'POST':
                for i in range(0, len(sid_list)):
                        if str(request.form['s_id']) == str(sid_list[i]):
                                error = 'Student ID already exists.'
                                return render_template("signup.html", error= error)
                if request.form['s_id'] == '':
                        error = 'Please enter Student ID.'
                        return render_template("signup.html",error=error)
                if request.form['password'] == '':
                        error = 'Please enter password.'
                        return render_template("signup.html",error=error)
                if str(request.form['password_confirm']) != str(request.form['password']):
                        error = 'Password confirm failed. Please signup again.'
                        return render_template("signup.html",error=error)

                else:
                        sid = request.form['s_id']
                        password = request.form['password']
                        value = (sid,password)
                        q = "insert into student values(%s, %s);"
                        g.conn.execute(q,value)
                        return render_template("success.html")

        return render_template("signup.html")

@app.route('/logout')
def logout():
        session.pop('logged_in', None)
        return render_template("index.html")

if __name__ == "__main__":
    import click
    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):

        HOST, PORT = host, port
        print "running on %s:%d" % (HOST, PORT)
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

    run()


