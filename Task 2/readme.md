- Be mindful of the timezone declared globally
- Talk about why using  SQL query instead of ORM

Knows Issues:
- If you use the same start and end date, it returns the data starting from the one day before the start date. This is occuring due to the timezone discrepancy. Fixing this from backend is less inefficient, rather should modify the database such way that it stores the date in UTC and then convert it to the local timezone when fetching. I will fix this if time allows.

To run:
cd "Task 2"
cd backend
uvicorn app.main:app --reload