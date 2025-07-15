- In the config file, there is a variable called GMT6, which is used in all other api endpoints. Initially the db was storing the date in GMT6, but now it is storing in UTC. This variable is not used anymore, but I have kept it for future use if needed.
- Talk about why using  SQL query instead of ORM

Knows Issues:
- If you use the same start and end date, it returns the data starting from the one day before the start date. This is occuring due to the timezone discrepancy. Fixing this from backend is less inefficient, rather should modify the database such way that it stores the date in UTC and then convert it to the local timezone when fetching. I will fix this if time allows.

To run:
cd "Task 2"
cd backend
uvicorn app.main:app --reload