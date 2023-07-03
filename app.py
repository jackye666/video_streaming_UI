from flask import Flask, render_template, Response, url_for, jsonify
import cv2
from flaskwebgui import FlaskUI
import sys
import threading
import random
import time
import keyboard
import argparse
import torch
import math
import numpy as np
import multiprocessing as mp
from torchvision import transforms, models
import torch.nn as nn
from PIL import Image
from std_msgs.msg import Int64, Float64MultiArray
from franka_msgs.msg import FrankaState
from scipy.spatial.transform import Rotation
import os
import rospy
from os.path import join
import logging
import copy


app = Flask(__name__,
            static_url_path='/static',
            static_folder='static')  # this is important for flask to read your css file, without indication of static url path and folder, css file won't be read properly.


camera = ""
isSave = False
saved_folder = "saved_frame"
mv_pred = "hold"
file = ""
args= ""


def calib_angle(ee_position):
    T1 = np.asarray(ee_position).reshape((4, 4)).T
    # angle = np.array([0.05675555627186434, 0.7781619195601319, 0.625494071737504, 0.0,
    #                   0.0795119019880618, -0.628036939167217, 0.7741107546622216, 0.0,
    #                   0.9952168930813586, 0.00579913682921899, -0.09751772012062157, 0.0,
    #                   0.29798168921190665, -0.1448472095247668, 0.7506857661469335, 1.0])
    # JN
    # angle = np.array([0.04708377235658972, 0.7813972391244601, 0.6222551510990844, 0.0,
    #                   0.07447851970792423, -0.6239582615150934, 0.7779004036437948, 0.0,
    #                   0.9961104700196606, 0.009718157013226774, -0.08757561841903876, 0.0,
    #                   0.2980300396445975, -0.12727154607479305, 0.7676168006362032, 1.0])
    # # LSQ
    # angle = np.array([ 0.14942991,  0.79438478,  0.58874742,  0,
    #                    0.1389825 , -0.60639603,  0.78292255,  0,
    #                    0.97895585, -0.03516646, -0.20101929,  0,
    #                    0.35941167, -0.25011404,  0.80949064,  1])

    # # SZG
    # angle = np.array([-0.09915866,  0.82699498,  0.55339576,  0,
    #                     0.10848553, -0.54383705,  0.83214912,  0,
    #                     0.98914026,  0.14255023, -0.03579083,  0,
    #                     0.31304733, -0.12770589,  0.81040914,  1])

    # SY
    angle = np.array([0.30909544, 0.77366372, 0.5530863, 0.,
                      0.18894045, -0.61992756, 0.76157162, 0.,
                      0.93207377, -0.13089794, -0.33779316, 0.,
                      0.35927308, -0.21256274, 0.82335111, 1.])

    T2 = angle.reshape((4, 4)).T
    T1_inv = np.linalg.inv(T1)  # 计算逆矩阵
    T_diff = np.dot(T1_inv, T2)  # 计算差值矩阵
    R_diff = T_diff[:3, :3]  # 提取旋转矩阵和平移向量
    r = Rotation.from_matrix(R_diff)  # 计算旋转矩阵的欧拉角表示
    rpy_diff = r.as_euler('xyz', degrees=False)
    res = [0, 0, 0] + list(rpy_diff)
    print(f'** res : {res} **')
    return res


class ArtificialSonographer:
    def __init__(self):
        # read probe angle, ee_position exists when flag_position=True
        self.flag_angle = False
        self.ee_position = None
        self.flag_position = False
        self.flag_contact = False
        # initiate inference process and send actions
        self.flag_scan = True  # when robotic arm holds still
        # stage
        self.flag_infrn = True  # run inference and publish actions when True
        self.flag_autoinf = False
        # action control
        self.pub = None
        self.pub2 = None
        self.signal_len = 100
        self.signal_list = []
        self.action = ord('s')
        self.stride = 1000
        self.flag_move = False
        self.flag_moving = False
        self.ee_force = None
        self.stop_signal = 0

    def Franka_cb(self, data):
        # read end effector position
        self.ee_position = data.O_T_EE
        self.flag_position = True
        self.ee_force = data.K_F_ext_hat_K

    def keyboard(self, data):
        cur_key = chr((data.data)).lower()
        # echo save switch
        if cur_key == 's':
            self.flag_infrn = not self.flag_infrn
            self.logger.info(f'{" ":<10}{"-" * 42}{" ":>10}\n'
                             f'{" ":<10}* Current state of [Process Switch]: '
                             f'{self.flag_infrn:^4} *{" ":>10}\n{" ":<10}{"-" * 42}{" ":>10}')
            if self.flag_infrn:
                self.logger.info(f'{"-" * 64}\n {">> Start model inference <<":^60} \n'
                                 f'{"-" * 64}\n')
            else:
                self.logger.info(f'{"-" * 64}\n {"<< Model inference paused >>":^60} \n'
                                 f'{"-" * 64}\n')
        elif cur_key == 'a':
            self.flag_angle = not self.flag_angle
            self.logger.info(f'{" ":<10}{"-" * 42}{" ":>10}\n'
                             f'{" ":<10}* Current state of [Angle Switch]: '
                             f'{self.flag_angle:^4} *{" ":>10}\n{" ":<10}{"-" * 42}{" ":>10}')

        elif cur_key == 'r':
            self.stride = 1000 + 10
            self.pub.publish(self.stride)
            self.logger.info(f'{" ":<10}{"-" * 42}{" ":>10}\n'
                             f'{" ":<10}* Current stride: '
                             f'{self.stride - 1000:^4} *{" ":>10}\n{" ":<10}{"-" * 42}{" ":>10}')
        elif cur_key == 'e':
            self.stride = 1000 + 2
            self.pub.publish(self.stride)
            self.logger.info(f'{" ":<10}{"-" * 42}{" ":>10}\n'
                             f'{" ":<10}* Current stride: '
                             f'{self.stride - 1000:^4} *{" ":>10}\n{" ":<10}{"-" * 42}{" ":>10}')

        elif cur_key == 'v':  # auto inference
            self.logger.info(
                f'{"-" * 64}\n {">> Start auto inference <<":^60} \n{"-" * 64}\n')
            self.flag_autoinf = True
            self.stop_signal = 0
        else:
            pass

    def action_control(self, msg):
        '''
        > Indicating action finish when receiving a full list of 1
          with length 'self.signal_len'
        > change self.signal_len for optimal performance
        '''
        self.signal_list.append(msg.data)
        self.logger.debug(f'* signal data: {msg.data} *')
        if len(self.signal_list) > self.signal_len:
            self.signal_list = self.signal_list[-self.signal_len:]

        if self.flag_move and not self.stride == 1000:
            self.flag_move = False
            self.pub.publish(self.stride)
            self.pub.publish(self.action)
            self.signal_list = []
            self.flag_moving = True

        if self.flag_moving and self.signal_list == [1] * self.signal_len:
            self.flag_moving = False
            self.flag_scan = True

    def init_log(self, log_root):
        # dir and name
        _, script_name = os.path.split(__file__)
        script_name_aff, _ = script_name.split('.')
        log_dir = join(log_root, script_name_aff)
        os.makedirs(log_dir, exist_ok=True)
        log_time = time.strftime('%Y%m%d_%H%M', time.localtime())
        log_path = join(log_dir, f'{log_time}.log')
        # config logger
        file_handler = logging.FileHandler(log_path, encoding="UTF-8")  # stdout to file
        console_handler = logging.StreamHandler()  # stdout to console
        # set level
        file_handler.setLevel('DEBUG')
        console_handler.setLevel('INFO')
        # output format
        log_fmt = '%(message)s'  # log_fmt = '[%(asctime)s] - <%(funcName)s> : %(levelname)s - %(message)s'
        log_fmt_file = '[%(asctime)s] - %(message)s'
        formatter = logging.Formatter(log_fmt)
        formatter_file = logging.Formatter(log_fmt_file)
        file_handler.setFormatter(formatter_file)
        console_handler.setFormatter(formatter)
        # set logger
        logger = logging.getLogger('logger')
        logger.setLevel('DEBUG')  # 设置了这个才会把debug以上的输出到控制台
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        self.logger = logger


def control(queue):
    ros_rate = 30  # Hz, for ros
    root = '/media/robotics1/WD_G_2T'
    aisono = ArtificialSonographer()  # AI Sonographer
    aisono.init_log(log_root=join(root, 'logs'))
    aisono.logger.info(f'\n{"=" * 64}\n {"Auto Echocardiography".center(60)}\n{"-" * 64}\n\n'
                       'Execute keyboard commands in "discrete_keyboard" terminal\n'
                       '1. To visualise video stream, press "c" \n'
                       '2. To initiate auto scanning, press "s" \n'
                       '3. To calibrate probe pose, press "a" \n'
                       '4. To bridge the gap between probe and chest,  press "b"')
    rospy.init_node('inference_vision', anonymous=True)
    aisono.pub = rospy.Publisher('keyboard', Int64, queue_size=10)
    aisono.pub2 = rospy.Publisher('vector_topic', Float64MultiArray, queue_size=10)
    rospy.Subscriber("keyboard", Int64, aisono.keyboard)
    rospy.Subscriber("/franka_state_controller/franka_states",
                     FrankaState, aisono.Franka_cb)
    # rospy.Subscriber('/my_heart_joint_velocity_setpoint_controller_vision/action_finished',
    #                  Int64, aisono.action_control)
    rospy.Subscriber('/my_heart_cartesian_impedance_controller/action_finished',
                     Int64, aisono.action_control)
    rate = rospy.Rate(ros_rate)

    while not rospy.is_shutdown():
        if aisono.flag_autoinf:
            aisono.flag_infrn = True

        # section 1.1: calib angle
        if aisono.flag_angle and not aisono.flag_move and not aisono.flag_moving:
            current_angles = calib_angle(aisono.ee_position)
            vector_msg = Float64MultiArray(data=current_angles)
            print(f'=> publish message: {current_angles}')
            aisono.pub2.publish(vector_msg)

            aisono.flag_angle = False
            aisono.logger.info(f'{" ":<10}{"-" * 42}{" ":>10}\n'
                               f'{" ":<10}* Current state of [Angle Switch]: '
                               f'{aisono.flag_angle:^4} *{" ":>10}\n{" ":<10}{"-" * 42}{" ":>10}')

        # section 2: inference (every 30 frames)
        if not aisono.flag_infrn:
            continue

        if aisono.flag_scan:
            # outputs = [x / 1000 for x in outputs[:3]] + [0, 0, 0]
            # outputs = [round(x, 5) for x in outputs]
            outputs = queue.get()
            stop_inference_signal = [x for x in outputs[:3] if abs(x) > 0.002]
            # print(stop_inference_signal)
            if len(stop_inference_signal) == 0:
                aisono.stop_signal += 1
            if aisono.stop_signal == 2:
                aisono.flag_autoinf = False
                aisono.flag_infrn = False

            vector_msg = Float64MultiArray(data=outputs)
            aisono.logger.info(f'=> publish message: {outputs}')
            aisono.pub2.publish(vector_msg)

        rate.sleep()

    aisono.cap.release()
    aisono.logger.info(f'{"-" * 64}\n {"Auto Echocardiography Complete":^60}\n{"=" * 64} ')


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
    crop_coord = (460, 140, 1200, 750)
    input_tensor = torch.zeros(30, 3, 224, 224)
    trans = transforms.Compose([
        transforms.Resize((224, 224)), transforms.ToTensor(),
        transforms.Normalize([0.193, 0.193, 0.193], [0.224, 0.224, 0.224])
    ])
    while True:
        # Capture frame-by-frame
        success, frame0 = camera.read()  # read the camera frame
        if not success:
            # break
            camera = cv2.VideoCapture(file)
        else:
            # print(frame.shape)
            frame = cv2.resize(frame0, (640, 480))
            if not args.simulate:
                print("#"*5+"True Prediction Mode"+"#"*5)
                if frame_count < 30:
                    frame_pre = frame0[crop_coord[1]:crop_coord[3], crop_coord[0]:crop_coord[2], :]
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
                        print(outputs)
            if isSave:
                cv2.imwrite(f'{saved_folder}/frame_{frame_count}.jpg', frame)
                isSave = False
            frame_count += 1
            max_frame += 1
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            time.sleep(0.05)
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


class Infer():
    def __init__(self, model_path, num_class, queue):
        self.model_path = model_path
        self.num_class = num_class
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.queue = queue

    def __load_model__(self):
        self.model = models.resnet34()
        self.model.fc = nn.Sequential(
            nn.Linear(self.model.fc.in_features, 256),
            nn.Dropout(0.4),
            nn.Linear(256, self.num_class))
        self.model.load_state_dict(torch.load(self.model_path))
        self.model.to(self.device)
        self.model.eval()
        return self.model

    def __call__(self, tensor):
        model = self.__load_model__()
        tensor = tensor.cuda() if torch.cuda.is_available() else tensor
        outputs = model(tensor)
        outputs, _ = torch.sort(outputs, dim=0)
        outputs = outputs[5:25, :]
        outputs = torch.mean(outputs, dim=0).tolist()
        action = self.rpy2action(outputs)
        outputs = [x / 1000 for x in outputs[:3]] + [x * math.pi / 180 for x in outputs[3:]]
        self.queue.put(outputs)
        return action

    def rpy2action(self, rpy: list):
        action_list = [["x+", "x-"], ["y+", "y-"], ["z+", "z-"], ["x_c", "x_a"], ["y_c", "y_a"], ["z_c", "z_a"]]
        max_stride = max([abs(x) for x in rpy])
        max_stride = max_stride if max_stride in rpy else -max_stride
        dim_action = rpy.index(max_stride)
        if max_stride < 0:
            a = -1
        else:
            a = 0
        action = action_list[dim_action][a]
        return action


def appshow(queue):
    global camera
    global inference

    # parser = argparse.ArgumentParser()
    # parser.add_argument("-g", "--gui", action="store_true", help="GUI mode")
    # parser.add_argument("-c", "--camera", action="store_true", help="Using camera")
    # parser.add_argument("-s", "--simulate", action="store_true", help="Simulate model inference")
    # args = parser.parse_args()
    inference = Infer(model_path='/media/robotics1/WD_2T/sunyu_data/models/6.29.pth', num_class=6, queue=queue)
    if args.simulate:
        thread1 = threading.Thread(target=sim_pred)
        thread1.start()

    file = 3 if args.camera else "static/video/out_slow.mp4"
    camera = cv2.VideoCapture(file)
    if args.gui:
        FlaskUI(app=app, server="flask", width=1300, height=780).run()
    else:
        app.run(debug=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--gui", action="store_true", help="GUI mode")
    parser.add_argument("-c", "--camera", action="store_true", help="Using camera")
    parser.add_argument("-s", "--simulate", action="store_true", help="Simulate model inference")
    args = parser.parse_args()
       
    queue = mp.Queue()  # Create a shared queue

    # Start the camera process
    camera_pro = mp.Process(target=appshow, args=(queue,))
    camera_pro.start()

    # Start the processing process
    if not args.simulate:
        processing = mp.Process(target=control, args=(queue,))
        processing.start()

    # Wait for processes to finish
    camera_pro.join()
    processing.join()

# python app.py -g -c