from flask import Flask, send_file, render_template, request, Response, redirect, url_for
import signal, os, time
from picamera import PiCamera
import pickle
import io, time, random
import numpy as np
from PIL import Image

app = Flask(__name__)

######### camera setting load #########
class Info:
        annotate = 'TEMP STRING'
        res1 = 1024
        res2 = 768
        bri = 50        
        pid = 0
'''
f = open('data.pickle', 'w')
MyInfo = Info()
pickle.dump(MyInfo, f)
f.close()
'''
f = open('data.pickle', 'r')
MyInfo = pickle.load(f)
f.close()


#####################################################
@app.route('/')
def start():
        return render_template('login.html')

@app.route('/index')
def index():
        return render_template('main.html')

#################### config page ####################
@app.route('/config')
def config():
        return render_template('config.html')

@app.route('/submit')
def submit():
        global MyInfo
        resolution = request.args.get('resolution', '')
        MyInfo.annotate = request.args.get('annotate', '')
        
        bri = request.args.get('brightness', '')
        if bri == '':
                MyInfo.bri = 50
        else:
                MyInfo.bri = int(bri)        

        if resolution == '1920x1080':
                MyInfo.res1 = 1920
                MyInfo.res2 = 1080
        elif resolution == '1280x720':
                MyInfo.res1 = 1280
                MyInfo.res2 = 720
        elif resolution == '1024x768':
                MyInfo.res1 = 1024
                MyInfo.res2 = 768
        elif resolution == '640x480':
                MyInfo.res1 = 640
                MyInfo.res2 = 480        

        save_config()       
        
        print(MyInfo.res1 + MyInfo.re2 + MyInfo.bri)
        return '0k'


@app.route('/capture')
def capture():
        with PiCamera() as camera:
                global MyInfo
                load_config()

                camera.resolution = (MyInfo.res1, MyInfo.res2)
                camera.brightness = MyInfo.bri
                camera.annotate_text = MyInfo.annotate

                image_file = open('image.jpg', 'wb')
                camera.capture(image_file)
                time.sleep(1)
                image_file.close()

        return send_file('image.jpg')

#################### streaming  ####################
@app.route('/streaming')
def streaming():   
    return redirect('/video_feed')

@app.route('/video_feed')
def video_feed():
    global MyInfo
    camera = PiCamera()
    load_config()
    camera.resolution = (MyInfo.res1, MyInfo.res2)
    camera.brightness = MyInfo.bri
    camera.annotate_text = MyInfo.annotate
    return Response(gen(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def gen(camera):
    try:
        while True:
            frame = get_frame(camera)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except:
        camera.close()

def get_frame(camera):
    stream = io.BytesIO()       
    camera.capture(stream, 'jpeg', use_video_port=True)
    stream.seek(0)  
    
    return stream.read()

#################### motion capture log view  ####################
@app.route('/log')
def log():        
        return render_template('log.html')
@app.route('/log_image')
def image_log():
        return render_template('log_image.html')

#################### common function module ####################
def save_config():
        f = open('data.pickle', 'w')
        global MyInfo        
        pickle.dump(MyInfo, f)
        f.close()

def load_config():
        f = open('data.pickle', 'r')
        global MyInfo
        MyInfo = pickle.load(f)
        f.close()

if __name__ == '__main__':            
        app.run('0.0.0.0', port=5000, threaded=True)

