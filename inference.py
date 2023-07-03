import os, time, logging, copy, cv2, rospy
import numpy as np
from PIL import Image
from numpy import pi
from os.path import join
from scipy.spatial.transform import Rotation
import torch.nn as nn
import torch
from torchvision import models
from torchvision import transforms as T
from math import pi as pp
from math import cos, sin
from std_msgs.msg import Int64, Float64MultiArray
from franka_msgs.msg import FrankaState


class ArtificialSonographer:
    def __init__(self, camera_id: int):
        # initiate video stream
        self.flag_stream = False
        self.cap = None
        self.crop_coord = (460, 140, 1200, 750)
        self.__init_stream__(camera_id)
        # initiate deep model
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.model_list = []
        self.trans = T.Compose([
            T.Resize((224, 224)), T.ToTensor(),
            T.Normalize([0.193, 0.193, 0.193], [0.224, 0.224, 0.224])
        ])
        # read probe angle, ee_position exists when flag_position=True
        self.flag_angle = False
        self.ee_position = None
        self.flag_position = False
        self.angle_dict = {(0, 1): '4', (0, -1): '6',
                           (1, 1): '5', (1, -1): '8',
                           (2, 1): '7', (2, -1): '9', }
        self.flag_contact = False
        # initiate inference process and send actions
        self.flag_scan = True  # when robotic arm holds still
        action_list = ['u', 'o', 'i', 'k', 'l', 'j',
                       '7', '9', '4', '6', '5', '8',
                       's', 'f']
        action_name = ['lift-up', 'press-down', 'move-up', 'move-down',
                       'move-left', 'move-right', 'roll-anti', 'roll',
                       'yaw-left', 'yaw-right', 'pitch-down', 'pitch-up',
                       'start', 'finished']
        self.action_dict = dict(zip(action_list, action_name))
        # self.action_ref = ['k', 'l', '6', '5', '7', 'f0', 'f1', 'f']
        self.action_ref = ['k', 'l', 'i', 'j', 'f']
        # stage
        self.flag_infrn = False  # run inference and publish actions when True
        self.flag_autoinf = False
        self.stage_ind = 0  # state index {0: state1, 1: stage2}
        self.flag_vote = False
        # action control
        self.pub = None
        self.pub2 = None
        self.signal_len = 100
        self.signal_list = []
        self.action = ord('s')
        self.stride = 1000
        self.action_count = 0
        self.flag_move = False
        self.flag_moving = False
        self.flag_force = False
        self.ee_force = None
        self.stop_signal = 0

    def __load_model__(self, model_path, num_class):
        model = models.resnet34()
        model.fc = nn.Sequential(
                nn.Linear(model.fc.in_features, 256),
                nn.Dropout(0.4),
                nn.Linear(256, num_class))
        model.load_state_dict(torch.load(model_path))
        model.to(self.device)
        model.eval()
        return model

    def __init_stream__(self, camera_id):
        cap = cv2.VideoCapture(camera_id)
        for _ in range(3):
            _, _ = cap.read()
        assert cap.isOpened(), f'\n{"=" * 69}\n *** ERROR: Invalid video stream. ' \
                               f'Check camera_id (0, 1, 2 or 3) or hws driver ***\n{"=" * 69}\n'
        self.cap = cap

    def streaming(self, flag, position):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.release()
            raise Exception('** Video stream terminated **')
        angles = [0, 0, 0]
        if flag:  # flag_position
            angles, _ = probe_angle(position)
        frame_show = frame[self.crop_coord[1]:self.crop_coord[3],
                     self.crop_coord[0]:self.crop_coord[2], :]
        return frame_show, angles

    def pred2action(self, vote_list):
        action = None
        for ind in range(len(vote_list)):
            stride = abs(vote_list[ind])
            if stride > 1:
                action = self.action_ref[self.stage_ind][ind]
                break
        if action is None:
            stride = 0
            action = 'f'
        return int(stride) + 1000, ord(action)

    def Franka_cb(self, data):
        # read end effector position
        self.ee_position = data.O_T_EE
        self.flag_position = True
        # read end effector force
        self.ee_force = data.K_F_ext_hat_K
        # self.logger.info(f'ee force: {self.ee_force}')

    def keyboard(self, data):
        cur_key = chr((data.data)).lower()
        # echo save switch
        if cur_key == 'c':
            self.flag_stream = not self.flag_stream
            self.logger.info(f'{" ":<10}{"-" * 42}{" ":>10}\n'
                             f'{" ":<10}* Current state of [Camera Switch]: '
                             f'{self.flag_stream:^4} *{" ":>10}\n{" ":<10}{"-" * 42}{" ":>10}')
        elif cur_key == 's':
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
        elif cur_key == 'z':
            self.logger.info(f'{" ":<10}{"-" * 42}{" ":>10}\n'
                             f'{" ":<19}* Launch probe to chest *'
                             f'{" ":>10}\n{" ":<10}{"-" * 42}{" ":>10}')
        elif cur_key == 'b':
            self.flag_contact = not self.flag_contact
            self.logger.info(f'{" ":<10}{"-" * 42}{" ":>10}\n'
                             f'{" ":<10}* Current state of [Contact Switch]: '
                             f'{self.flag_contact:^4} *{" ":>10}\n{" ":<10}{"-" * 42}{" ":>10}')
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
            action = chr(self.action)
            self.pub.publish(self.stride)
            self.pub.publish(self.action)
            self.signal_list = []
            self.flag_moving = True
            action_name = self.action_dict[action]
            self.logger.info(f'\t=> #{self.action_count:03d}-{action} '
                             f'stride-{self.stride - 1000} | "{action_name}"')
            if not self.flag_contact:
                os.system(f'spd-say "{action_name}" ')
        if self.flag_moving and self.signal_list == [1] * self.signal_len:
            self.flag_moving = False
            self.flag_scan = True
            action_name = self.action_dict[chr(self.action)]
            self.logger.info(f'\t=> Action "{action_name}" complete \n{"-" * 48}')
            os.system(f'spd-say "done"')

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


def calc_angles(arr):
    beta = np.arctan(-arr[2, 0] / (np.sqrt(arr[0, 0] * arr[0, 0] + arr[1, 0] * arr[1, 0]))) / pi * 180
    alpha = np.arctan(arr[1, 0] / np.cos(beta) / (arr[0, 0] / np.cos(beta))) / pi * 180
    if alpha < 0:
        alpha += 180
    gamma = np.arctan(arr[2, 1] / np.cos(beta) / (arr[2, 2] / np.cos(beta))) / pi * 180
    return [beta, alpha, gamma]


def probe_angle(ee_position):
    arr1 = np.asarray(ee_position).reshape((4, 4)).T
    arr2 = np.array([[-1e-9, -1, -1e-9],
                     [-1, 1e-9, -1e-9],
                     [1e-9, 1e-9, -1]])
    [beta1, alpha1, gamma1] = calc_angles(arr1)
    [beta2, alpha2, gamma2] = calc_angles(arr2)

    angle_diffs = np.array([gamma1 - gamma2, beta1 - beta2, alpha1 - alpha2])
    return [np.around(angle_diffs, 1), [beta1, alpha1, gamma1]]


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
    angle = np.array([  0.30909544,  0.77366372,  0.5530863 ,  0.        ,
                        0.18894045, -0.61992756,  0.76157162,  0.        ,
                        0.93207377, -0.13089794, -0.33779316,  0.        ,
                        0.35927308, -0.21256274,  0.82335111,  1.        ])

    T2 = angle.reshape((4, 4)).T
    T1_inv = np.linalg.inv(T1)  # 计算逆矩阵
    T_diff = np.dot(T1_inv, T2)  # 计算差值矩阵
    R_diff = T_diff[:3, :3]  # 提取旋转矩阵和平移向量
    r = Rotation.from_matrix(R_diff)  # 计算旋转矩阵的欧拉角表示
    rpy_diff = r.as_euler('xyz', degrees=False)
    res = [0, 0, 0] + list(rpy_diff)
    print(f'** res : {res} **')
    return res


# --------------------------------- lsq 0621 -------------------------------------


def transformedMatrix(originalMatrix):
    rotation_z = np.eye(4)
    rotation_z[:3, :3] = rotate_3d(np.pi, 'z')

    rotation_y = np.eye(4)
    rotation_y[:3, :3] = rotate_3d(-np.pi / 2, 'y')

    return np.dot(np.dot(originalMatrix, rotation_z), rotation_y)


def rotate_3d(theta, axis):
    if axis == 'x':
        rotation_matrix = np.array([[1, 0, 0],
                                    [0, cos(theta), -sin(theta)],
                                    [0, sin(theta), cos(theta)]])
    elif axis == 'y':
        rotation_matrix = np.array([[cos(theta), 0, sin(theta)],
                                    [0, 1, 0],
                                    [-sin(theta), 0, cos(theta)]])
    elif axis == 'z':
        rotation_matrix = np.array([[cos(theta), -sin(theta), 0],
                                    [sin(theta), cos(theta), 0],
                                    [0, 0, 1]])
    else:
        raise ValueError("Invalid axis value. Please choose 'x', 'y', or 'z'.")

    return rotation_matrix


# ---------------------------------


def main():
    # params
    script_code = 'CV'  # identify vision from RL or other fields
    ros_rate = 30  # Hz, for ros
    max_frame = 30
    camera_id = 3  # for StreamVideo
    num_classes = 6
    root = '/media/robotics1/WD_G_2T'
    # init object
    aisono = ArtificialSonographer(camera_id)  # AI Sonographer
    aisono.init_log(log_root=join(root, 'logs'))
    aisono.logger.info(f'\n{"=" * 64}\n {"Auto Echocardiography".center(60)}\n{"-" * 64}\n\n'
                       'Execute keyboard commands in "discrete_keyboard" terminal\n'
                       '1. To visualise video stream, press "c" \n'
                       '2. To initiate auto scanning, press "s" \n'
                       '3. To calibrate probe pose, press "a" \n'
                       '4. To bridge the gap between probe and chest,  press "b"')

    model_path = '/media/robotics1/WD_2T/sunyu_data/models/6.29.pth'
    aisono.logger.info(f'\n {"-- >>":>21} {"preparing models ... ":^20}{"<< --":<21} ')
    aisono.model = aisono.__load_model__(model_path, num_classes)

    aisono.logger.info(f' {"-- >>":>21} {"model ready ":^20}{"<< --":<21}\n')
    date = time.strftime('%Y%m%d-%H%M', time.localtime())
    save_root = join(root, 'inference_record', f'{script_code}_{date}')
    # ros
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
    # counters
    input_tensor = torch.zeros((max_frame, 3, 224, 224))
    frame_count = 0
    angle_count = 0
    img_list = []
    aisono.logger.info(f'\n{" | ":->24} {"Stage":>9} {aisono.stage_ind:<4} {" | ":-<24}')
    while not rospy.is_shutdown():
        if aisono.flag_autoinf:
            aisono.flag_infrn = True

        # section 1: video stream
        frame, angles = aisono.streaming(aisono.flag_position, aisono.ee_position)
        frame_show = copy.deepcopy(frame)
        if aisono.flag_stream:
            cv2.putText(frame_show, f'{angles[0]}, {angles[1]}, {angles[2]}', (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (173, 206, 230), 1, 8, 0)
            cv2.imshow("UltrasoundStream", frame_show)  # 173, 206, 230; 205, 179, 139
            cv2.waitKey(1)
        else:
            cv2.destroyAllWindows()
            cv2.waitKey(1)

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
            if frame_count < max_frame:
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                img_list.append(img)
                input_tensor[frame_count, :, :, :] = aisono.trans(img)
                frame_count += 1
                continue
            elif frame_count == max_frame:  # 30 frames gathered, ready for publishing action
                frame_count = 0
                aisono.action_count += 1
                aisono.flag_scan = False
                aisono.flag_vote = True
            else:
                aisono.logger.info(f'** ERROR: abnomal frame count: {frame_count} **')

        # section 3: max vote, publish stride and action
        if aisono.flag_vote:
            aisono.flag_vote = False
            input_mean = input_tensor.mean(dim=0)
            fuse_tensor = torch.zeros((max_frame, 3, 224, 224))
            for i in range(input_tensor.shape[0]):
                fuse_tensor[i, :, :, :] = input_mean * 0.6 + input_tensor[i, :] * 0.4

            with torch.no_grad():
                outputs = aisono.model(fuse_tensor.to(aisono.device))

            # 去掉极值，取平均
            outputs, _ = torch.sort(outputs, dim=0)
            outputs = outputs[5:25, :]
            outputs = torch.mean(outputs, dim=0).tolist()
            # outputs = [round(x, 4) for x in outputs]
            # 转换格式 （m to mm, degree to arc）
            outputs = [x / 1000 for x in outputs[:3]] + [0, 0, 0]
            outputs = [round(x, 5) for x in outputs]
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

            # save images with action
            save_dir = join(save_root, f'{aisono.action_count:03d}-{chr(aisono.action)}')
            os.makedirs(save_dir, exist_ok=True)
            for img_ind, img in enumerate(img_list):
                img.save(join(save_dir, f'{img_ind:03d}.jpg'))

            img_list = []
            input_tensor = torch.zeros((max_frame, 3, 224, 224))
            aisono.flag_scan = True
            aisono.flag_infrn = False

        rate.sleep()

    aisono.cap.release()
    aisono.logger.info(f'{"-" * 64}\n {"Auto Echocardiography Complete":^60}\n{"=" * 64} ')


class Infer():
    def __init__(self, model_path, num_class):
        self.model_path = model_path
        self.num_class = num_class
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        
    def __load_model__(self):
        self.model = models.resnet34()
        self.model.fc = nn.Sequential(
            nn.Linear(model.fc.in_features, 256),
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
        outputs = [x / 1000 for x in outputs[:3]] + [0, 0, 0]
        return outputs