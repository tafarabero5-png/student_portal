from flask import Flask, render_template,request,redirect,session
import pymysql
import requests
app= Flask(__name__)
app.secret_key='tafara victor'

#database  connection function
def get_database():
    return pymysql.connect(host='localhost',user='root',password="victor", database='fca_ereport',
                           cursorclass=pymysql.cursors.DictCursor);

#login for the teacher
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = (request.form['password'].encode())
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
    cursor = conn.cursor(pymysql.cursors.DictCursor)

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

        return redirect('/marks_success')
    else:
        # On GET, load students to show the form
        class_id = request.args.get('class_id')
        subject_id = request.args.get('subject_id')
        term = request.args.get('term')

        if not (class_id and subject_id and term):
            return redirect('/select_class')

        conn = get_database()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
                      SELECT s.id, s.firstname, s.surname
        FROM students s
        JOIN student_subjects ss ON s.id = ss.student_id
        WHERE ss.subject_id = %s AND s.class_id = %s
    """, (subject_id, class_id))
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
    term = 'Term 1'  # You can add term input later

    conn = get_database
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
@app.route('/marks_success')
def mark_success():
    return render_template('marks_success.html')

#SEND REPORTS TO PARENTS
@app.route('/send',methods=['GET','POST'])
def send_reports():
    if 'teacher_id' not in session:
        return redirect('/')
    
    if request.method=='POST':
        term=request.form['term']
        conn=get_database()
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM students")
        students=cursor.fetchall()

        for student in students:
         student_id=student['id']
         name=student['name']
         phone=student['parent_phone']

         cursor.execute("""
                SELECT subject, score FROM marks
                WHERE student_id=%s AND term=%s
            """, (student_id, term))

        marks=cursor.fetchall()
        if not marks:
         msg = f"Report for {name} ({term}):\n"
        total = 0
        for m in marks:
                msg += f"- {m['subject']}: {m['score']}\n"
        

        #send whatsapp message using chat API
    payload={"phone":phone, "body":msg}
    requests.post("https://api.chat-api.com/instanceXXXX/sendMessage?token=YOUR_TOKEN",json=payload)
    conn.close()
    return "REPORTS SENT SUCCESSFULLY!"
    return 
    render_template('send_reports.html')


#LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

#run app
if __name__=='_main_':
 app.run(debug=True)
