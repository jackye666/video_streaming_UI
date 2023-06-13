from flask import Flask, render_template, Response, url_for, jsonify
import cv2
from flaskwebgui import FlaskUI
import sys
import threading
import random
import time
import keyboard

app = Flask(__name__,
        static_url_path='/static',
        static_folder='static')#this is important for flask to read your css file, without indication of static url path and folder, css file won't be read properly.

# camera = cv2.VideoCapture(-1)  # use 0 for web camera
camera = cv2.VideoCapture(0)
# ui = FlaskUI(app,width=1400, height=980)
# for cctv camera use rtsp://username:password@ip_address:554/user=username_password='password'_channel=channel_number_stream=0.sdp' instead of camera
# for local webcam use cv2.VideoCapture(0)
isSave = False
saved_folder = "saved_frame"
mv_pred = "hold"

def gen_pred():
    global mv_pred
    mvs = ["x+","x-","y+","y-"]
    while True:
        i = random.randint(0,3)
        with threading.Lock():
            mv_pred = mvs[i]
        time.sleep(2)
        print(mv_pred)
        
        if keyboard.is_pressed('i'):
            print("Interrupted!")
            break
        
    print("END")
    return

def gen_frames():  # generate frame by frame from camera
    global isSave
    frame_count = 0
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            # print(frame.shape)
            frame = cv2.resize(frame, (640,480))
            if isSave:
                cv2.imwrite(f'{saved_folder}/frame_{frame_count}.jpg',frame)
                isSave=False
            frame_count+=1
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

@app.route('/img_name')
def get_img_name():
    # img_list = {"name":["PLAX","PSAX-AV","PSAX-MV","PSAX-PM","AP4","AP5","AP2","None"],\
        # "diagram":["d1","d2","d3","d4","d5","d6","d7","None"],"position":["p1","p234","p234","p234","p5","p5","p5"]}
    img_list = {"PLAX":{"category":["PLAX","None"],"diagram":["d1"],"position":["p1"]},\
                "PSAX":{"category":["PSAX-AV","PSAX-MV","PSAX-PM","None"],"diagram":["d2","d3","d4","None"],"position":["p234","p234","p234"]},\
                "AP":{"category":["AP2","AP4","AP5","None"],"diagram":["d7","d5","d6","None"],"position":["p5","p5","p5"]}    }
    return img_list

@app.route('/save_img')
def save_img():
    global isSave
    isSave = True
    return "Saved"

@app.route('/move_prediction')
def get_move_pred():
    return mv_pred


if __name__ == '__main__':
    # print(sys.argv)
    thread1 = threading.Thread(target=gen_pred)
    thread1.start()
        
    argv = sys.argv
    if len(argv) > 1 and sys.argv[1] == "gui":
        FlaskUI(app=app, server="flask",width=1300, height=780).run()
    else:
        app.run(debug=True)
    