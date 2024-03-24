from flask import Flask, render_template, Response,request,redirect,session,send_from_directory
import os
from flask import send_from_directory
from flask_login import login_required
import cv2
import pyaudio
import json
import audioop
import pymysql.cursors
import numpy as np
import face_recognition
import os
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'bsddsjvGVVJ876483jVJV'
connection = pymysql.connect(host='localhost',
                             user='root',
                             password='@g209X1A05H6g@',
                             database = 'students'            
                             )
cursor = connection.cursor()

audio = pyaudio.PyAudio()
stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
path = 'ImagesAttendance'
images = []
classNames = []
myList = os.listdir(path)
name_global=''
print(myList)
for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])
print(classNames)

def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList
 
def markAttendance(name):
    with open('Attendance.csv','r+') as f:
        myDataList = f.readlines()
        nameList = []
        for line in myDataList:
            entry = line.split(',')
            nameList.append(entry[0])
        if name not in nameList:
            now = datetime.now()
            dtString = now.strftime('%H:%M:%S')
            f.writelines(f'\n{name},{dtString}')


encodeListKnown = findEncodings(images)
print('Encoding Complete')
def verify_face():
    cap = cv2.VideoCapture(0)
    while True:
        ret, img = cap.read()

        if not ret:
            break
        imgS = cv2.resize(img,(0,0),None,0.25,0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        facesCurFrame = face_recognition.face_locations(imgS)
        encodesCurFrame = face_recognition.face_encodings(imgS,facesCurFrame)
    
        for encodeFace,faceLoc in zip(encodesCurFrame,facesCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown,encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown,encodeFace)
            matchIndex = np.argmin(faceDis)
    
            if matches[matchIndex]:
                name = classNames[matchIndex].upper()
                #print(name)
                y1,x2,y2,x1 = faceLoc
                y1, x2, y2, x1 = y1*4,x2*4,y2*4,x1*4
                cv2.rectangle(img,(x1,y1),(x2,y2),(0,255,0),2)
                cv2.rectangle(img,(x1,y2-35),(x2,y2),(0,255,0),cv2.FILLED)
                cv2.putText(img,name,(x1+6,y2-6),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),2)
                global name_global
                name_global=name
                markAttendance(name)
        ret, buffer = cv2.imencode('.jpg', img)
        if not ret:
            continue
        img = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n')

def generate_frames():
    max_blink_count = 5  
    blink_counter = 0
    cap = cv2.VideoCapture(0)
    prev_eye_state = True
    tab_switch_detected = False
    noise_detected = False
    noise_reset_counter = 0
    noise_reset_threshold = 40 
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        audio_data = stream.read(1024)
        rms = audioop.rms(audio_data, 2)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) == 0:
            cv2.putText(frame, "Face Not Detected!", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y + h, x:x + w]
            eyes = cv2.Canny(roi_gray, 100, 200)
            eye_state = True  
            contours, _ = cv2.findContours(eyes, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 1000:  
                    eye_state = False  
            if eye_state != prev_eye_state:
                prev_eye_state = eye_state
                if not eye_state:
                    blink_counter += 1
            key = cv2.waitKey(1)
            if key == 9:  
                tab_switch_detected = True
            if rms > 300: 
                noise_detected = True
                noise_reset_counter = 0
            else:
                if noise_reset_counter < noise_reset_threshold:
                    noise_reset_counter += 1
                else:
                    noise_detected = False

            if blink_counter > max_blink_count or noise_detected:
                cv2.putText(frame, "Suspicious Activity Detected!", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return redirect('/home')

@app.route('/dashboard')
def dashboard():
    if 'rollno' in session:
        data=[]
        cursor = connection.cursor()
        sql="select * from `stu_data` where rollno="+str(session['rollno'])+";"
        cursor.execute(sql)

        for i in cursor:
            data.append(list(i))
        cursor.close()
        print(data)
        return render_template('dashboard.html',data=data)
    return redirect('/home')
    
@app.route('/home', methods=['GET', 'POST'])
def login():
    if 'rollno' in session:
        return redirect('/dashboard')
    if request.method == 'POST':
        roll = request.form['rollno']
        pwd = request.form['pwd']
        data=[]
        cursor = connection.cursor()
        sql="select * from `stu_details` where rollno="+str(roll)+";"
        cursor.execute(sql)
        for i in cursor:
            data.append(list(i))
        cursor.close()
        print(roll,pwd,data)
        if(data[0][0]==roll.strip() and data[0][1]==pwd.strip()):
            session['rollno'] = roll
            return redirect('/dashboard')
        else :
            return "<h2 style='color:red;'> Invalid Password </h2> <a href='/home'>Goback</a>"
    return render_template('home.html')

@app.route('/protected/<path:filename>')
def protected(filename):
    if filename=='quiz.html':
        datac=[]
        cursor = connection.cursor()
        sql="select * from `quiz_results` where rollno="+str(session['rollno'])+";"
        cursor.execute(sql)
        for i in cursor:
            datac.append(list(i))
        cursor.close()
        if(len(datac)>0):
            return "<h2 style='color:red;'>You Have Already Taken the Test</h2> <br> <a href='/home'>Go Back</a>"
        
        elif 'rollno' in session and session['rollno']==name_global:
            print(name_global)
            return send_from_directory('protected', filename)
        elif 'rollno' in session and session['rollno']!=name_global :
            return "<h2 style='color:red;'>User is Not Matched with our DataBase</h2> <a href='/dashboard'>Goback</a>"
    else :
        return send_from_directory('protected', filename)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/auth_video_feed')
def auth_video_feed():
    return Response(verify_face(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/logout')
def logout():
    session.pop('rollno', None)
    return redirect('/')

@app.route('/store-quiz-result', methods=['POST'])
def result():
    data = request.get_json()
    print(data['percentage'])
    try:
        cursor = connection.cursor()
        sql='''insert into `quiz_results`(rollno,marks)values(%s,%s)'''
        v=[str(session.get('rollno')),str(data['percentage'])]
        cursor.execute(sql,v)
        connection.commit()
        cursor.close()
        return f'data: Success'
    except Exception as e:
        print(e)
        return f'data: Failed'

@app.route('/auth')
def auth():
    return render_template('auth.html')

@app.route('/results')
def res():
    data=[]
    cursor = connection.cursor()
    sql="select * from `quiz_results`;"
    cursor.execute(sql)

    for i in cursor:
        data.append(list(i))
    cursor.close()
    
    if(len(data)==0):
        return "<h2 style='color:red;'>Results Not Yet Available</h2> <br> <a href='/home'>Go Back</a>"
    else:
        return render_template('results.html',data=data)



@app.route('/stu-data')
def stu_details():
    data=[]
    cursor = connection.cursor()
    sql="select * from `stu_data`;"
    cursor.execute(sql)

    for i in cursor:
        data.append(list(i))
    cursor.close()
    return render_template('student_data.html',data=data)



@app.route("/ImagesAttendance/<path:filename>")
def profilephoto(filename):
    return send_from_directory('ImagesAttendance', filename)


    
@app.errorhandler(404) 
def not_found(e): 
    return "<h2>404 Not Found</h2> <a href='/home'>Goback</a>"

if __name__ == '__main__':
    app.run(debug=True,port=5056)
