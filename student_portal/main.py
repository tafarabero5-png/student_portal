from flask import Flask, render_template, request, redirect, session
import pymysql
import os

app = Flask(__name__)
app.secret_key = 'tafara victor'

#Database connection function
def get_database():
    return pymysql.connect(host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        
        cursorclass=pymysql.cursors.DictCursor
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
      cursor=conn.cursor(pymysql.cursors.DictCursor)
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
        student_id = request.form['id']  # Adjusted to match login form field
        session['student_id'] = student_id
    else:
        student_id = session.get('student_id')
        term=session.get('term')

    if not student_id:
        return redirect('/')

    conn = get_database()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM students WHERE id=%s", (student_id,))
    student = cursor.fetchone()

    if not student:
        return "Student not found"

    cursor.execute("""
    SELECT s.name AS subject, m.score,
    CASE 
        WHEN m.score >= 75 THEN 'A'
        WHEN m.score >= 65 THEN 'B'
        WHEN m.score >= 50 THEN 'C'
        WHEN m.score >= 40 THEN 'D'
        ELSE 'O'
    END AS grade
    FROM marks m
    JOIN subjects s ON m.subject_id = s.id
    WHERE m.student_id = %s AND m.term=%s
""", (student_id,term))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('student_results.html', student=student, results=results,term=term)


#Entry point
if __name__ == 'main':
    app.run(debug=True, port=5001)


