from flask import Flask, render_template, request, redirect, session
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)
app.secret_key = 'tafara victor'

#Database connection function
def get_database():
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_NAME')

    # Debug prinT
    print(f"Connecting with: host={host}, user={user}, database={database}")

    if not all([host, user, password, database]):
        raise Exception("One or more environment variables are missing!")
    return psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    dbname=os.getenv("DB_NAME"),
    cursor_factory=psycopg2.extras.DictCursor
)

#Student login page
@app.route('/', methods=['GET','POST'])
def student_login():
    if request.method=='POST':
      firstname=request.form['firstname']
      surname=request.form['surname']
      student_id=request.form['id']
      term=request.form['term']
      conn=get_database()
      cursor=conn.cursor()

      cursor.execute("SELECT * FROM students WHERE Firstname=%s AND Surname=%s AND id=%s",(firstname,surname,student_id))
      student=cursor.fetchone()
      conn.close()
      if student:
          session['student_id']=student['id']
          session['term']=term
          return redirect('/student_portal')
      else:
          return "STUDENT NOT FOUND!!!!"
    return render_template('student_login.html')

#student view the results
@app.route('/student_portal', methods=['GET', 'POST'])
def student_portal():
     if request.method == 'POST':
        student_id = request.form.get('id')
        term = request.form.get('term')
        session['student_id'] = student_id
        session['term'] = term
     else:
        student_id = session.get('student_id')
        term = session.get('term')

     if not student_id or not term:
        return redirect('/')

     conn = get_database()
     cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
     # Fetch student info along with their class name
     cursor.execute("""
        SELECT s.*, c.name as class_name
        FROM students s
        JOIN classes c ON s.class_id = c.id
        WHERE s.id = %s
     """, (student_id,))
     student = cursor.fetchone()
     if not student:
      return "Student not found"

#Fetch marks for the student and term
     cursor.execute("""
     SELECT sub.name AS subject, m.score,
     CASE 
        WHEN m.score >= 75 THEN 'A'
        WHEN m.score >= 65 THEN 'B'
        WHEN m.score >= 50 THEN 'C'
        WHEN m.score >= 40 THEN 'D'
        WHEN m.score >= 30 THEN 'E'
        ELSE 'O'
    END AS grade
    FROM marks m
    JOIN subjects sub ON m.subject_id = sub.id
    WHERE m.student_id = %s AND m.term = %s
""", (student_id, term))

     results = cursor.fetchall()
     cursor.close()
     conn.close()

     return render_template('student_results.html', student=student, results=results, term=term)



#Entry point
if __name__ == '__main__':
    app.run(debug=True, port=5001)
    