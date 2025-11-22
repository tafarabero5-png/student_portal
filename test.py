import pymysql
def get_database():
    return pymysql.connect(  host='sql10.freesqldatabase.com',
         user='sql10808959',
        password='uXxkwd2L3E',
        database='sql10808959',

                           cursorclass=pymysql.cursors.DictCursor);
try:
    connection = get_database()
    print("✅ Connected to the database successfully!")
    connection.close()
except Exception as e:
    print("❌ Connection failed:")
    print(e)

