from flask import Flask, render_template, Response
import cv2
from flaskwebgui import FlaskUI
import threading
import random
import time
import argparse
import multiprocessing as mp

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static')  # this is important for flask to read your css file, without indication of static url path and folder, css file won't be read properly.


camera = ""
isSave = False
saved_folder = "static/saved_frame"
mv_pred = "hold"
file = ""
img_cnt = 0

parser = argparse.ArgumentParser()
parser.add_argument("-g", "--gui", action="store_true", help="GUI mode")
parser.add_argument("-c", "--camera", action="store_true", help="Using camera")
parser.add_argument("-s", "--simulate", action="store_true", help="Simulate model inference")
args = parser.parse_args()


def sim_pred():
    global mv_pred
    # mvs = ["hold","x+","x-","z+","z-","y-","y+","z_c","z_a","y_c","y_a","x_a","x_c"]
    mvs = ["x-","x+","y-","y+","hold","x_c","y_c","y_a"]
    # mvs = ["hold","x_c"]
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
    global mv_pred
    global QS
    global file
    global args
    global queue
    global l
    global act
    global send_flag
    global quality_score
    global img_cnt
    frame_count = 0
    max_frame = 0
    msg = ["x+", "x-", "y+", "y-", "z+", "z-", "x_c", "x_a", "y_c", "y_a", "z_c", "z_a", "hold"]
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
            frame = cv2.resize(ori_frame, (640, 480))
            if not args.simulate:
                if max_frame < 30:
                    frame_pre = ori_frame[crop_coord[1]:crop_coord[3], crop_coord[0]:crop_coord[2], :]
                    img = Image.fromarray(cv2.cvtColor(frame_pre, cv2.COLOR_BGR2RGB))
                    input_tensor[max_frame, :, :, :] = trans(img)

                if max_frame == 29:
                    input_mean = input_tensor.mean(dim=0)
                    fuse_tensor = torch.zeros((30, 3, 224, 224))
                    for i in range(input_tensor.shape[0]):
                        fuse_tensor[i, :, :, :] = input_mean * 0.6 + input_tensor[i, :] * 0.4
                    queue.put(fuse_tensor)
                    input_tensor = torch.zeros(30, 3, 224, 224)

                if send_flag.value:
                    max_frame = -1
                    mv_pred = msg[act.value]
                    QS = quality_score.value
                    l.acquire()
                    send_flag.value = 0
                    l.release()
            if isSave:
                cv2.imwrite(f'{saved_folder}/img_{img_cnt}.jpg', frame)
                isSave = False
                img_cnt += 1
            frame_count += 1
            max_frame += 1
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            time.sleep(0.02);
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
    return f'{saved_folder}/img_{img_cnt}.jpg'


@app.route('/move_prediction')
def get_move_pred():
    return mv_pred

i=0
@app.route("/get_score")
def get_quality_score():
    if args.simulate:
        global i
        i+=1*2
        val = 0+i/5
        if val >= 100:
            i = 0
            val = 0 + i/5
        return str(val)
    else:
        return str(QS)

if __name__ == '__main__':
    queue = mp.Queue()  # Create a shared queue
    l = mp.Lock()  # 定义一个进程锁
    act = mp.Value('i', -1)   # 当前影像需要执行的动作
    send_flag = mp.Value('i', 0)   # 默认False，每次预测机械臂运动结束后为True，来执行下一次操作
    quality_score = mp.Value('i', 0)   # 质量得分
    if not args.simulate:
        from infer import control
        processing = mp.Process(target=control, args=(queue, l, act, send_flag, quality_score))
        processing.start()

    # Wait for processes to finish
    if args.simulate:
        thread1 = threading.Thread(target=sim_pred)
        thread1.daemon = True
        thread1.start()
    file = 1 if args.camera else "static/video/out_slow.mp4"
    camera = cv2.VideoCapture(file)
    if args.gui:
        FlaskUI(app=app, server="flask", width=1300, height=780).run()
    else:
        app.run(debug=True)
    if not args.simulate:
        processing.join()

# python app.py -g -c
