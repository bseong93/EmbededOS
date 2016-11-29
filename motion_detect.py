from flask import Flask, render_template, Response, redirect
from picamera import PiCamera
import io, time, random
import numpy as np
from PIL import Image
import pickle
import subprocess

###
MyInfo = None

class Info:
        annotate = 'TEMP STRING'
        res1 = 1024
        res2 = 768
        bri = 50        
        pid = 0

prior_image = None
threshold = 30
width = 320
height = 240
minPixelsChanged = (width * height) * 2 / 100
###


app = Flask(__name__)

@app.route('/')
def index():   
    return redirect('/video_feed')

@app.route('/video_feed')
def video_feed():
    global MyInfo
    camera = PiCamera()
    load_config()
    camera.resolution = (MyInfo.res1, MyInfo.res2)
    camera.brightness = MyInfo.bri
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
    global MyInfo
    stream = io.BytesIO()       
    camera.capture(stream, 'jpeg', use_video_port=True)
    stream.seek(0)

    
    camera.resolution = (320, 240)
    capture_motion(camera)
    camera.resolution = (MyInfo.res1, MyInfo.res2)
    
    return stream.read()

def load_config():
        f = open('data.pickle', 'r')
        global MyInfo
        MyInfo = pickle.load(f)
        f.close()

######################## capture motion #####################
image_name = []
def capture_motion(camera):
    global image_name
    if detect_motion(camera):
        print('Motion detected!')                
        FileName = time.strftime("%Y%m%d-%H%M%S-.jpg",time.localtime())

        image_file = open( "static/" + FileName , 'wb')
        camera.annotate_text = time.strftime("[%Y.%m.%d]%H:%M:%S",time.localtime())
        camera.capture(image_file)
        image_file.close()
                
        log_file = open('templates/log.html', 'a+')
        log_file.write('<h2>' + FileName + ' image detection!!</h2>\n')
        log_file.close()

        image_log_file = open('templates/log_image.html', 'a+')
        image_log_file.write('<img src="{{url_for(\'static\', filename=\'' +
                             FileName + '\')}}">\n ')
        image_log_file.close()
        ##        
        image_name += [FileName]
        
        if len(image_name) == 5:                
                for i in range(len(image_name)):
                        subprocess.Popen( 'mpack -s "' + image_name[i] + '" /home/pi/Final_Project/static/' + image_name[i] + ' sksmscjswodi@hanmail.net', shell=True)                       
                image_name = []
                       
        #subprocess.Popen( 'mpack -s "motion detection" /home/pi/Final_Project/static/' + FileName + ' 1004genius@naver.com', shell=True)        
        ##
      
        print('Motion stopped!')

######################## detect motion #####################
def detect_motion(camera):
    global prior_image
    stream = io.BytesIO()   
    camera.capture(stream, 'rgba',True)
    stream.seek(0)
    if prior_image is None:
        stream.seek(0)
        prior_image = np.fromstring(stream.getvalue(), dtype=np.uint8)
        return False
    else:
        stream.seek(0)
        current_image = np.fromstring(stream.getvalue(), dtype=np.uint8)#
        data3 = np.abs(prior_image - current_image) 
        result = np.count_nonzero(data3 > threshold) / 4 / threshold

        if result > minPixelsChanged:
            result = 1
        else:
            result = 0
        prior_image = current_image
        return result


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, threaded=True)
