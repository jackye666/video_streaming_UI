from flask import Flask, render_template, Response, url_for, jsonify
import cv2
from flaskwebgui import FlaskUI

app = Flask(__name__,
        static_url_path='/static',
        static_folder='static')#this is important for flask to read your css file, without indication of static url path and folder, css file won't be read properly.

# camera = cv2.VideoCapture(-1)  # use 0 for web camera
camera = cv2.VideoCapture('static/video/1.mp4')
# ui = FlaskUI(app,width=1400, height=980)
# for cctv camera use rtsp://username:password@ip_address:554/user=username_password='password'_channel=channel_number_stream=0.sdp' instead of camera
# for local webcam use cv2.VideoCapture(0)

def gen_frames():  # generate frame by frame from camera
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            # print(frame.shape)
            frame = cv2.resize(frame, (640,480))
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
    img_list = {"name":["PLAX","PSAX-AV","PSAX-MV","PSAX-PM","AP4","None"],"diagram":["d1","d2","d3","d4","d5","None"],"position":["p1","p234","p234","p234","p5"]}
    return jsonify(img_list)


if __name__ == '__main__':
    app.run(debug=True)
    # FlaskUI(app=app, server="flask",width=1300, height=780).run()