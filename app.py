from flask import Flask, render_template, Response, url_for, jsonify
import cv2
from flaskwebgui import FlaskUI
import sys
import threading
import random
import time
import keyboard
import argparse

app = Flask(__name__,
        static_url_path='/static',
        static_folder='static')#this is important for flask to read your css file, without indication of static url path and folder, css file won't be read properly.

# camera = cv2.VideoCapture(-1)  # use 0 for web camera
# file = "static/video/out_slow.mp4"
# camera = cv2.VideoCapture(file)
camera = ""
# ui = FlaskUI(app,width=1400, height=980)
# for cctv camera use rtsp://username:password@ip_address:554/user=username_password='password'_channel=channel_number_stream=0.sdp' instead of camera
# for local webcam use cv2.VideoCapture(0)
isSave = False
saved_folder = "saved_frame"
mv_pred = "hold"

def gen_pred():
    global mv_pred
    mvs = ["hold","x+","x-","z+","z-","y-","y+","z_c","z_a","y_c","y_a","x_a","x_c"]
    # mvs = ["x_c","x_a"  ]
    while True:
        i = random.randint(0,len(mvs)-1)
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
    global camera
    frame_count = 0
    while True:
        # Capture frame-by-frame
        # if not camera.isOpend():
            
            # cv2.VideoCapture("static/video/out_slow.mp4")
        success, frame = camera.read()  # read the camera frame
        if not success:
            # break
            camera = cv2.VideoCapture(file)
        else:
            # print(frame.shape)
            frame = cv2.resize(frame, (640,480))
            if isSave:
                cv2.imwrite(f'{saved_folder}/frame_{frame_count}.jpg',frame)
                isSave=False
            frame_count+=1
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            time.sleep(0.05)
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
    thread1 = threading.Thread(target=gen_pred)
    thread1.start()
    parser = argparse.ArgumentParser()
    parser.add_argument("-g","--gui",action="store_true",help="GUI mode")
    parser.add_argument("-c","--camera",action="store_true",help="Using camera")
    args = parser.parse_args()
    # argv = sys.argv
    # if len(argv) > 1 and sys.argv[1] == "gui":
    #     FlaskUI(app=app, server="flask",width=1300, height=780).run()
    # else:
    #     app.run(debug=True)
    file = 0 if args.camera else "static/video/out_slow.mp4"
    camera = cv2.VideoCapture(file)
    if args.gui:
        FlaskUI(app=app, server="flask",width=1300, height=780).run()
    else:
        app.run(debug=True)
        
    
