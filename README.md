# IOT_Project_2016

MON2 project:SmartSeats

Distribution of the python file:
1. ColletDataAnalysis.py
loops through all the installed sensors and connects to each one via Bluetooth. we use tool[i].expect to read values from the 1st Notification or the 2nd Notification, and use tool[i].after.split() to read the bytes that represent the sensor values we would like to use. 

The two elements we use for judgement are:
* We detect temperature different due to the body temperature from the occupant. 
* For every set of sensors connected to one Edison, Acceleration in the vertical direction (denoted AccZ) is used for our movement indicator.
The two elements combined together could help us get rid of the noice to get a more reliable judgement of the occupation. Like if the environment temperture goes up or when someone rotate the chair accidentally. It would make one of the indicator become "occupied" but only when two of the elements becomes "occupied" could we say that the seat is occupied. When one of "occupied" comes, we make it an uncertain situation which would be shown in our web site visulization.

2.DataToDynamodb.py
For this part, we used the segment of code we used in the previous lab experient to push data to dynamoDB. We create a new table in dynamoDB and set up the configuration in our program so that our data that update in the cloud could be caught from anywhere. The main data is the collecting data and the result of our data analysis. In our program, we used Temperature and Movement as indicator to judge whether the seat have been occupied. And the data would be saved in a csv file which we will use for the future data analysis use.

3.plot.py
We used ipython to visualize 
