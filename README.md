# IOT_Project_2016

MON2 project:SmartSeats

Distribution of the python file:

--DATA COLLECT AND ANALYSIS

1. ColletDataAnalysis.py
loops through all the installed sensors and connects to each one via Bluetooth. we use tool[i].expect to read values from the 1st Notification or the 2nd Notification, and use tool[i].after.split() to read the bytes that represent the sensor values we would like to use. 

The two elements we use for judgement are:
* We detect temperature different due to the body temperature from the occupant. 
* For every set of sensors connected to one Edison, Acceleration in the vertical direction (denoted AccZ) is used for our movement indicator.
The two elements combined together could help us get rid of the noice to get a more reliable judgement of the occupation. Like if the environment temperture goes up or when someone rotate the chair accidentally. It would make one of the indicator become "occupied" but only when two of the elements becomes "occupied" could we say that the seat is occupied. When one of "occupied" comes, we make it an uncertain situation which would be shown in our web site visulization.

2.DataToDynamodb.py
For this part, we used the segment of code we used in the previous lab experient to push data to dynamoDB. We create a new table in dynamoDB and set up the configuration in our program so that our data that update in the cloud could be caught from anywhere. The main data is the collecting data and the result of our data analysis. In our program, we used Temperature and Movement as indicator to judge whether the seat have been occupied. And the data would be saved in a csv file which we will use for the future data analysis use.

3.plot.py
We used ipython to visualize our seat occupation situation with the data we get from dynamoDB.


--DATA VISUALIZATION ON WEBSITE (flask-Smart-seat-realtime)

We used a simple python-based website designed package, flask to build our website. The main page includes two parts of our seat situation. 

1. seat reservation sytstem
It's connected with postgreSQL database which is used for storing student information, seat information and reservation situation. The main functions include: 
a complete login system. Users could sign up an account. Same ID name or unmatched confirm password would be forbidden
a complete reservation system. Users could reserve seat in a certain time period. Reserve an unavailable seat is not allowed. Besides, one user could not reserve multiple seats in the same time period. Data in database would upgrade simultaneously with the action of users.

2. real-time seat occupation visualization
The Edison periodically sends seat status to AWS DynamoDB, which stores the most updated occupancy information for each seat. From the DynamoDB our website retrieves the updates, and display them to our users in a straightforward mapping that reflects how the seats are physically arranged in the library. Each seat belongs to one of the three possible categories:

* Empty (RELIABLE): Both temperature and acceleration criteria indicate the seat is available
* Occupied (RELIABLE): Both temperature and acceleration criteria indicate the seat is unavailable
* Uncertain (UNRELIABLE): Only one of the temperature and acceleration criteria indicates that the seat is occupied
Below is an example of the user interface, showing six seats, their statuses, and how they are arranged in the library.
