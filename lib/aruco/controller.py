import math
import cv2
import numpy as np
from . import Camera
from . import transformations
from . import PID
from timeit import default_timer as timer

ERROR = 0.15

class Controller:
    def __init__(self, S, dir_queue, navigate_event):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.dir_queue = dir_queue
        self.navigate_event = navigate_event

        self.camera = Camera('calibration_files/camcalib.npz')
        self.amplify = 10
        self.speed = S
        self.TargetID = 1
        self.t_lost = 1
        self.last_marker_pos = 1
        
        self.yaw_pid = PID(0.1, 0.00001, 0.001)
        self.v_pid = PID(0.5, 0.00001, 0.0001)
        self.vz_pid = PID(0.8, 0.00001, 0.0001)
        self.TargetPos = np.array([[0., 0., 1., 0.]])

    def calibrate(self, frame):
        return self.camera.calibrate(frame)

    def detect(self, frame):
        frame, id_list, rvecs, tvecs, corners, w, h = self.camera.detect(frame)
        
        if self.TargetID in id_list:
            index = id_list.index(self.TargetID)
            x1 = 0
            x2 = tvecs[index][0][0]
            y1 = 0
            y2 = tvecs[index][0][1]
            z1 = 0
            z2 = tvecs[index][0][2]
            distance = math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2) + math.pow(z2 - z1, 2))
            cv2.putText(frame, f"{round(distance, 2)} m", (0,64), self.font, 1, (0,0,255),2,cv2.LINE_AA)

        if len(id_list) > 0:
            if self.navigate_event.is_set():
                frame = self.drawCenter(frame, id_list, corners, w, h)
                directions = self.navigateToTarget(id_list, tvecs, rvecs)
        else:
            if timer()-self.t_lost > 2:
                if self.last_marker_pos >= 0:
                    self.dir_queue.put([0, 0, 0, self.speed * 2])
                else:
                    self.dir_queue.put([0, 0, 0, -self.speed * 2])

        return frame

    def navigateToTarget(self, id_list, rvecs, tvecs):
        if self.TargetID not in id_list:
            if timer() - self.t_lost > 1:
                if self.last_marker_pos >= 0:
                    self.dir_queue.put([0, 0, 0, self.speed * 2])
                else:
                    self.dir_queue.put([0, 0, 0, -self.speed * 2])
        else:
            index = id_list.index(self.TargetID)
            tvec = tvecs[index]
            rvec = rvecs[index]

            self.last_marker_pos = tvec[0][0]
            rvec = transformations.rotationVectorToEulerAngles(rvec) * 180 / math.pi
        
            if abs(rvec[0][2]) > 90:
                rvec[0][1] = -rvec[0][1]

            directions = [0., 0., 0., 0.]
            A = self.amplify * self.speed
            
            err_yaw = rvec[0][1] - self.TargetPos[0][3]
            directions[3] = self.speed / 2 * self.yaw_pid.control(err_yaw)

            err_x = self.TargetPos[0][0] - tvec[0][0]
            directions[0] = -A * self.v_pid.control(err_x)
            err_y = self.TargetPos[0][2] - tvec[0][2]
            directions[1] = -A * self.v_pid.control(err_y)
            err_z = self.TargetPos[0][1] - tvec[0][1]
            directions[2] = A * self.vz_pid.control(err_z)

            self.t_lost = timer()
            self.dir_queue.put(directions)
            return directions

    def drawCenter(self, frame, seen_id_list, corners, w, h):
        if self.TargetID not in seen_id_list:
            pass
        else:
            ind = seen_id_list.index(self.TargetID)
            cx = int((corners[ind][0][0][0]+corners[ind][0][1][0]+corners[ind][0][2][0]+corners[ind][0][3][0])/4)
            cy = int((corners[ind][0][0][1]+corners[ind][0][1][1]+corners[ind][0][2][1]+corners[ind][0][3][1])/4)
            cv2.line(frame, (int(w/2), int(h/2)), (cx, cy), (0,255,255), 3)
        
        return frame