from flask import Flask, render_template, Response, url_for, jsonify
import cv2
from flaskwebgui import FlaskUI
import sys
import threading
import random
import time
import keyboard
import argparse
import multiprocessing as mp

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static')  # this is important for flask to read your css file, without indication of static url path and folder, css file won't be read properly.

inference = ""
camera = ""
isSave = False
saved_folder = "saved_frame"
mv_pred = "hold"
file = ""

parser = argparse.ArgumentParser()
parser.add_argument("-g", "--gui", action="store_true", help="GUI mode")
parser.add_argument("-c", "--camera", action="store_true", help="Using camera")
parser.add_argument("-s", "--simulate", action="store_true", help="Simulate model inference")
args = parser.parse_args()


def sim_pred():
    global mv_pred
    # mvs = ["hold","x+","x-","z+","z-","y-","y+","z_c","z_a","y_c","y_a","x_a","x_c"]
    mvs = ["z_c", "z_a", "y_c", "y_a", "x_a", "x_c"]
    while True:
        i = random.randint(0, len(mvs) - 1)
        with threading.Lock():
            mv_pred = mvs[i]
        time.sleep(2)
        print(mv_pred)

        # if keyboard.is_pressed('i'):
        #     print("Interrupted!")
        #     break

    print("END")
    return


def gen_frames():  # generate frame by frame from camera
    global isSave
    global camera
    global inference
    global mv_pred
    global file
    global args
    frame_count = 0
    max_frame = 0

    if not args.simulate:
        from torchvision import transforms
        from PIL import Image
        import torch
        crop_coord = (460, 140, 1200, 750)
        input_tensor = torch.zeros(30, 3, 224, 224)
        trans = transforms.Compose([
            transforms.Resize((224, 224)), transforms.ToTensor(),
            transforms.Normalize([0.193, 0.193, 0.193], [0.224, 0.224, 0.224])
        ])
    while True:
        # Capture frame-by-frame
        success, ori_frame = camera.read()  # read the camera frame
        if not success:
            file = 3 if args.camera else "static/video/out_slow.mp4"
            try:
                camera = cv2.VideoCapture(file)
            except Exception as e:
                print(file)
                break
        else:
            # print(frame.shape)
            frame = cv2.resize(ori_frame, (640, 480))
            if not args.simulate:
                if frame_count < 30:
                    frame_pre = ori_frame[crop_coord[1]:crop_coord[3], crop_coord[0]:crop_coord[2], :]
                    img = Image.fromarray(cv2.cvtColor(frame_pre, cv2.COLOR_BGR2RGB))
                    input_tensor[frame_count, :, :, :] = trans(img)

                if max_frame == 30:
                    input_mean = input_tensor.mean(dim=0)
                    fuse_tensor = torch.zeros((30, 3, 224, 224))
                    for i in range(input_tensor.shape[0]):
                        fuse_tensor[i, :, :, :] = input_mean * 0.6 + input_tensor[i, :] * 0.4

                    input_tensor = torch.zeros(30, 3, 224, 224)
                    with torch.no_grad():
                        outputs = inference(fuse_tensor)
                        max_frame = 0
                        mv_pred = outputs
            if isSave:
                cv2.imwrite(f'{saved_folder}/frame_{frame_count}.jpg', frame)
                isSave = False
            frame_count += 1
            max_frame += 1
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # time.sleep(0.05)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


@app.route('/video_feed')
def video_feed():
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


@app.route('/img_name')
def get_img_name():
    # img_list = {"name":["PLAX","PSAX-AV","PSAX-MV","PSAX-PM","AP4","AP5","AP2","None"],\
    # "diagram":["d1","d2","d3","d4","d5","d6","d7","None"],"position":["p1","p234","p234","p234","p5","p5","p5"]}
    img_list = {"PLAX": {"category": ["PLAX", "None"], "diagram": ["d1"], "position": ["p1"]}, \
                "PSAX": {"category": ["PSAX-AV", "PSAX-MV", "PSAX-PM", "None"], "diagram": ["d2", "d3", "d4", "None"],
                         "position": ["p234", "p234", "p234"]}, \
                "AP": {"category": ["AP2", "AP4", "AP5", "None"], "diagram": ["d7", "d5", "d6", "None"],
                       "position": ["p5", "p5", "p5"]}}
    return img_list


@app.route('/save_img')
def save_img():
    global isSave
    isSave = True
    return "Saved"


@app.route('/move_prediction')
def get_move_pred():
    return mv_pred


def appshow(queue):
    global camera
    global inference
    global args

    if args.simulate:
        thread1 = threading.Thread(target=sim_pred)
        thread1.start()
    else:
        from infer import Infer
        inference = Infer(model_path='/media/robotics1/WD_2T/sunyu_data/models/6.29.pth', num_class=6, queue=queue)

    file = 3 if args.camera else "static/video/out_slow.mp4"
    camera = cv2.VideoCapture(file)
    if args.gui:
        FlaskUI(app=app, server="flask", width=1300, height=780).run()
    else:
        app.run(debug=True)


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument("-g", "--gui", action="store_true", help="GUI mode")
    # parser.add_argument("-c", "--camera", action="store_true", help="Using camera")
    # parser.add_argument("-s", "--simulate", action="store_true", help="Simulate model inference")
    # args = parser.parse_args()

    queue = mp.Queue()  # Create a shared queue

    # Start the camera process
    camera_pro = mp.Process(target=appshow, args=(queue,))
    camera_pro.start()

    # Start the processing process
    if not args.simulate:
        from infer import control
        processing = mp.Process(target=control, args=(queue,))
        processing.start()

    # Wait for processes to finish
    camera_pro.join()
    if not args.simulate:
        processing.join()

# python app.py -g -c