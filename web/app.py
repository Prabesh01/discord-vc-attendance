from flask import Flask, render_template, jsonify, request, redirect
from functools import wraps
import json
import os
import requests

app = Flask(__name__, static_url_path='/static')

basepath=os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.dirname(basepath) +'/data'
from dotenv import load_dotenv
load_dotenv(data_dir+'/.env')


def fetch_data(at=None):
    with open(data_dir+'/attendance.json') as f:
        attendance_data = json.load(f)
    if at: return attendance_data
    
    with open(data_dir+'/user.json') as f:
        users_data = json.load(f)
        
    return users_data, attendance_data


def get_attendance_data():
    users_data, attendance_data=fetch_data()
    user_attendace={}
    attendance_days=[]
    for user in users_data:
        _data=users_data[user]
        _data['attendance']=[]
        user_attendace[user]=_data
    for date in attendance_data:
        attendance_days.append({date:len(attendance_data[date])})
        for user in users_data:
            user_attendace[user]['attendance'].append(1 if user in attendance_data[date] else 0)

    filtered_users = {user: data for user, data in user_attendace.items() if sum(data['attendance']) > 0}
    sorted_users = sorted(filtered_users.items(), key=lambda item: sum(item[1]['attendance']), reverse=True)
    sorted_user_attendace = {user: data for user, data in sorted_users}

    return sorted_user_attendace, attendance_days


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/attendance')
def get_attendance():
    user_attendace, attendance_days=get_attendance_data()
    return render_template('attendance.html',user_attendace=user_attendace, attendance_days=attendance_days)


def check_auth(username, password):
    return username == os.getenv('HTTP_AUTH_USER') and os.getenv('HTTP_AUTH_PASSWORD') == password

def authenticate():
    return jsonify({'success': False, 'message': 'Authentication required'}), 401, {
        'WWW-Authenticate': 'Basic realm="Login Required"'
    }

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.get('/admin')
@requires_auth
def admin_get():
    user_attendace, attendance_days=get_attendance_data()
    return render_template('admin.html',user_attendace=user_attendace, attendance_days=attendance_days)


@app.post('/admin')
@requires_auth
def admin_post():
    data = request.json
    user_id = data.get('userId')
    date = data.get('date')
    is_present = data.get('status')

    attendance_data=fetch_data(1)
    user_exists = user_id in attendance_data[date]
    if not is_present and user_exists:
        attendance_data[date].remove(user_id)
    if is_present and not user_exists:
        attendance_data[date].append(user_id)
    with open(data_dir+'/attendance.json', 'w') as f:
        json.dump(attendance_data, f, indent=4)
    
    return "", 200


@app.get('/backup')
@requires_auth
def backup():
    for file in ['user', 'attendance']:
        file_path=data_dir+'/'+file+'.json'
        f=open(file_path,'rb')
        requests.post(os.getenv("data_backup_webhook"), files={"file": f})
        f.close()

    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)
