from std_msgs.msg import Int64, Float64MultiArray
from franka_msgs.msg import FrankaState
from scipy.spatial.transform import Rotation
from torchvision import models
import os
import rospy
import logging
import torch
import torch.nn as nn
import math
import numpy as np
import time


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


class Infer():
    def __init__(self, model_path, num_class):
        self.model_path = model_path
        self.num_class = num_class
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.model = self.__load_model__()

    def __load_model__(self):
        model = models.resnet34()
        model.fc = nn.Sequential(
            nn.Linear(model.fc.in_features, 256),
            nn.Dropout(0.4),
            nn.Linear(256, self.num_class))
        model.load_state_dict(torch.load(self.model_path))
        model.to(self.device)
        model.eval()
        warm_x = torch.randn(30, 3, 224, 224).cuda()
        warm_out = model(warm_x)
        return model

    def __call__(self, tensor):
        tensor = tensor.cuda() if torch.cuda.is_available() else tensor
        outputs = self.model(tensor)
        outputs, _ = torch.sort(outputs, dim=0)
        outputs = outputs[5:25, :]
        outputs = torch.mean(outputs, dim=0).tolist()
        action = self.rpy2action(outputs)
        outputs = [x / 1000 for x in outputs[:3]] + [x * math.pi / 180 for x in outputs[3:]]
        return action, outputs

    def rpy2action(self, rpy: list):
        action_list = [["x+", "x-"], ["y+", "y-"], ["z+", "z-"], ["x_c", "x_a"], ["y_c", "y_a"], ["z_c", "z_a"]]
        msg = ["x+", "x-", "y+", "y-", "z+", "z-", "x_c", "x_a", "y_c", "y_a", "z_c", "z_a"]
        max_stride = max([abs(x) for x in rpy])
        max_stride = max_stride if max_stride in rpy else -max_stride
        dim_action = rpy.index(max_stride)
        if max_stride < 0:
            a = -1
        else:
            a = 0
        action = action_list[dim_action][a]
        action_num = msg.index(action)
        return action_num

class ArtificialSonographer:
    def __init__(self, l, send_flag):
        # read probe angle, ee_position exists when flag_position=True
        self.flag_angle = False
        self.ee_position = None
        self.flag_position = False
        self.flag_contact = False
        # initiate inference process and send actions
        self.flag_scan = True  # when robotic arm holds still
        # stage
        self.flag_infrn = False  # run inference and publish actions when True
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
        self.l = l
        self.send_flag = send_flag

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
        self.signal_list.append(msg.data)
        self.logger.debug(f'* signal data: {msg.data} *')
        if len(self.signal_list) > self.signal_len:
            self.signal_list = self.signal_list[-self.signal_len:]

        if self.flag_move and not self.stride == 1000:
            self.flag_move = False
            self.signal_list = []
            self.flag_moving = True

        if self.flag_moving and self.signal_list == [1] * self.signal_len:
            self.l.acquire()
            self.send_flag.value = 1
            self.l.release()
            self.flag_moving = False
            self.flag_scan = True

    def init_log(self, log_root):
        _, script_name = os.path.split(__file__)
        script_name_aff, _ = script_name.split('.')
        log_dir = os.path.join(log_root, script_name_aff)
        os.makedirs(log_dir, exist_ok=True)
        log_time = time.strftime('%Y%m%d_%H%M', time.localtime())
        log_path = os.path.join(log_dir, f'{log_time}.log')
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


def control(queue, l, act, send_flag):
    inference = Infer(model_path='/media/robotics1/WD_2T/sunyu_data/models/6.29.pth', num_class=6)
    ros_rate = 30  # Hz, for ros
    root = '/media/robotics1/WD_G_2T'
    aisono = ArtificialSonographer(l, send_flag)  # AI Sonographer
    aisono.stride = 1001
    aisono.init_log(log_root=os.path.join(root, 'logs'))
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

        if not aisono.flag_moving and aisono.flag_scan:
            fuse_tensor = queue.get()
            with torch.no_grad():
                action, outputs = inference(fuse_tensor)
                l.acquire()
                act.value = action
                l.release()
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
            aisono.flag_move = True
            aisono.flag_infrn = False

        rate.sleep()

    aisono.cap.release()
    aisono.logger.info(f'{"-" * 64}\n {"Auto Echocardiography Complete":^60}\n{"=" * 64} ')


