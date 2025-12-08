from flask import Flask,session,render_template,redirect,request
import requests
app=Flask(__name__)
app.secret_key=('tafaravictor')
#SEND REPORTS TO PARENTS
def get_database():
    ()

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
