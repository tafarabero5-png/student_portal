from flask import Flask, render_template,request,redirect,session, url_for
import requests
import psycopg2
import psycopg2.extras

from dotenv import load_dotenv
load_dotenv()

import os
app= Flask(__name__)
app.secret_key='tafara victor'

#database  connection function
def get_database():
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_NAME')

    # Debug print (optional, remove later)
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

#login for the teacher
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teachers WHERE username=%s AND password=%s", (username, password))
        teacher = cursor.fetchone()
        conn.close()
        if teacher:
            session['teacher'] = teacher['username']
            
            return redirect('/select_class')
        else:
            return "oops invalid credentials!!"
    return render_template('login.html')


#teacher selects the class to input marks
@app.route('/select_class', methods=['GET', 'POST'])
def select_class():
    if 'teacher' not in session:
        return redirect('/')

    conn = get_database()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  

    if request.method == 'POST':
        class_id = request.form['class_id']
        subject_id = request.form['subject_id']
        term = request.form['term']

        conn.close()

        return redirect(f"/enter_marks?class_id={class_id}&subject_id={subject_id}&term={term}")

    # Fetch classes
    cursor.execute("SELECT id, name FROM classes")
    classes = cursor.fetchall()

    # Fetch all subjects with class_id for filtering in HTML
    cursor.execute("""
                   select cs.class_id,s.id,s.name
                   FROM class_subjects cs
                   JOIN subjects s on cs.subject_id=s.id
                   """)
    subjects = cursor.fetchall()

    terms = ['Term 1', 'Term 2', 'Term 3']
    conn.close()

    return render_template('select_class.html', classes=classes, subjects=subjects, terms=terms)

#enter marks for the students
@app.route('/enter_marks', methods=['GET', 'POST'])
def enter_marks():
    if 'teacher' not in session:
        return redirect('/')

    errors = {}
    if request.method == 'POST':
        class_id = request.form['class_id']
        subject_id = request.form['subject_id']
        term = request.form['term']
    
        marks = []
        conn = get_database()
        cursor = conn.cursor()

        for key in request.form:
            if key.startswith('mark_'):
                student_id = key.split('_')[1]
                score = request.form[key].strip()

                if not score:
                    errors[student_id] = "Mark is required"
                else:
                    cursor.execute("""
                        SELECT id FROM marks 
                        WHERE student_id = %s AND subject_id = %s AND term = %s
                    """, (student_id, subject_id, term))
                    existing = cursor.fetchone()
                    if existing:
                        errors[student_id] = "Mark has already been entered for this term"
                    else:
                        marks.append((student_id, subject_id, term, score))

        if errors:
            cursor.close()
            conn.close()
            return f"Errors: {errors}", 400

        for student_id, subject_id, term, score in marks:
            cursor.execute("""
                INSERT INTO marks (student_id, subject_id, term, score)
                VALUES (%s, %s, %s, %s)
            """, (student_id, subject_id, term, score))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('mark_success', subject_id=subject_id))


    else:
        # On GET, load students to show the form
        class_id = request.args.get('class_id')
        subject_id = request.args.get('subject_id')
        term = request.args.get('term')
        
        if not (class_id and subject_id and term):
            return redirect('/select_class')

        conn = get_database()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        
    cursor.execute("""
        SELECT s.id, s.firstname, s.surname
        FROM students s
        JOIN student_subjects ss ON s.id = ss.student_id
        WHERE ss.subject_id = %s AND s.class_id = %s
        """
    , (subject_id, class_id))
    students = cursor.fetchall()

    # Fetch class name
    cursor.execute("SELECT name AS class_name FROM classes WHERE id = %s", (class_id,))
    class_row = cursor.fetchone()
    class_name = class_row['class_name'] if class_row else 'Unknown Class'

    # Fetch subject name
    cursor.execute("SELECT name FROM subjects WHERE id = %s", (subject_id,))
    subject_row = cursor.fetchone()
    subject_name = subject_row['name'] if subject_row else 'Unknown Subject'




    conn.close()
    return render_template('enter_marks.html',
                           students=students,
                           class_id=class_id,
                           subject_id=subject_id,
                           class_name=class_name,
                           subject_name=subject_name,
                           term=term,
                           errors=errors)




#saving the marks entered by the teacher
@app.route('/save_marks', methods=['POST'])
def save_marks():
    class_id = session.get('class_id')
    term = 'Term 1'  

    conn = get_database()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM students WHERE class_id = %s", (class_id,))
    student_ids = [row[0] for row in cursor.fetchall()]

    for student_id in student_ids:
        subject = request.form.get(f"subject_{student_id}")
        score = request.form.get(f"score_{student_id}")

        if subject and score:
            cursor.execute("SELECT id FROM subjects WHERE name = %s", (subject,))
            subject_row = cursor.fetchone()

            if not subject_row:
                cursor.execute("INSERT INTO subjects (name) VALUES (%s)", (subject,))
                conn.commit()
                subject_id = cursor.lastrowid
            else:
                subject_id = subject_row[0]
            cursor.execute("INSERT INTO marks (student_id, subject_id, score, term) VALUES (%s, %s, %s, %s)",
                           (student_id, subject_id, score, term))

    conn.commit()
    cursor.close()
    conn.close()
    return "Marks Saved Successfully"
#returning back to the  login page
@app.route('/marks_success/<int:subject_id>')
def mark_success(subject_id):
     conn=get_database()
     cursor=conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
     #suject name
     cursor.execute("select name from  subjects  where id =%s ",(subject_id,))
     subject=cursor.fetchone()
     subject_name=subject['name'] if subject else "unknown"
     #class name
     cursor.execute("select name from classes where id=%s",(subject_id,))
     classes=cursor.fetchone()
     class_name=classes['name'] if classes else "unknown class"
                    
     
    #total students who do that subject
     cursor.execute("select count(distinct student_id) from marks where subject_id=%s",(subject_id,))
     total_students=cursor.fetchone()[0]
     # Top performer (based on highest mark)
     cursor.execute("""
        SELECT s.firstname || ' ' || s.surname AS name, MAX(m.score) as max_score
        FROM marks m
        JOIN students s ON s.id = m.student_id
                    where m.subject_id=%s
        GROUP BY s.id
        ORDER BY  max_score DESC
        LIMIT 1;
                    """,(subject_id,))
     top_performer = cursor.fetchone()
     #passrate for the subject
     cursor.execute("""
        SELECT  
               ROUND(COUNT(*) FILTER (WHERE m.score >= 50)::numeric / COUNT(*) * 100, 2) AS pass_rate
        FROM marks as m
        where m.subject_id=%s
    """,(subject_id,))
     pass_rate=cursor.fetchone()['pass_rate']
     #top 5 students
     cursor.execute("""
                    select s.firstname || ' ' || s.surname AS name,m.student_id,m.score 
                    from marks m
                    join students s on s.id=m.student_id
                    where m.subject_id=%s
                    order by m.score desc
                    limit 5
                    """,(subject_id,))
     top_5=cursor.fetchall()
     #bottom 5 students
     cursor.execute(""" select s.firstname || ' ' || s.surname AS name,m.student_id,m.score
                    from marks m
                    join students s on s.id=m.student_id
                    where m.subject_id=%s
                    order by m.score asc
                    limit 5
""",(subject_id,))
     bottom_5=cursor.fetchall()
     
     return render_template('marks_success.html',subject_name=subject_name,total_students=total_students,
                            top_5=top_5, bottom_5=bottom_5,class_name=class_name,top_performer=top_performer,pass_rate=pass_rate)



#LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

#run app
if __name__=='_main_':
 app.run(debug=True)
