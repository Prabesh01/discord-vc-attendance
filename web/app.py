from flask import Flask, render_template, send_from_directory
import json
import os
from datetime import datetime

app = Flask(__name__, static_url_path='/static')

basepath=os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.dirname(basepath) +'/data'

with open(data_dir+'/user.json') as f:
    users_data = json.load(f)

with open(data_dir+'/attendance.json') as f:
    attendance_data = json.load(f)


def get_attendance_data():
    user_attendace={}
    attendance_days=[]
    for user in users_data:
        _data=users_data[user]
        _data['attendance']=[]
        user_attendace[user]=_data
    for date in attendance_data:
        attendance_days.append(datetime.strptime(date, '%Y-%m-%d').strftime("%d %b"))
        for user in users_data:
            user_attendace[user]['attendance'].append(1 if user in attendance_data[date] else 0)
    return user_attendace, attendance_days


@app.route('/')
def display_attendance():
    user_attendace, attendance_days=get_attendance_data()
    return render_template('attendance.html',user_attendace=user_attendace, attendance_days=attendance_days)
    

if __name__ == '__main__':
    app.run(debug=True)
