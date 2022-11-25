This is the server file to handle incoming event requests from the client javascript hosted here https://github.com/adi2907/clickstream

Refer this write-up for a detailed explanation of the setup and logic https://www.adiganguli.com/2022/11/01/diy-clickstream-framework-2-events-storage-in-database/


It is a simple Django instance and divided as follows

1. Events app within Django which listens to events through urls.py
2. views.py responding to URL events/ and saving to model created
3. models.py has the sample database structure


Appropriate changes need to be done on settings.py viz allowed host,allowing cors and disabling crsf checks. Details in the writeup shared above 

auth folder stores the configurations required. In this case, a username to access mysql database. This can be ignored since you can use root to access the mysql database

