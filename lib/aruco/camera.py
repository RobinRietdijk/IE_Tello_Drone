import cv2
import numpy as np
import configparser
import queue
import time
from timeit import default_timer as timer
from config import CONFIG
from .aruco_dict import ARUCO_DICT

ARUCO_TYPE = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[CONFIG['Aruco']['type']])
BOARD_COLS = CONFIG['Aruco']['board_cols']
BOARD_ROWS = CONFIG['Aruco']['board_rows']
BOARD_HEIGHT = CONFIG['Aruco']['board_height']
BOARD_WIDTH = CONFIG['Aruco']['board_width']
BOARD_SQUARE_LENGTH = CONFIG['Aruco']['board_square_length']
BOARD_MARKER_LENGTH = CONFIG['Aruco']['board_marker_length']
MARKER_LENGTH = CONFIG['Aruco']['marker_length']

S_PROG = CONFIG['Camera']['s_prog']

board = cv2.aruco.CharucoBoard((BOARD_COLS, BOARD_ROWS), BOARD_SQUARE_LENGTH, BOARD_MARKER_LENGTH, ARUCO_TYPE)

class Camera():
    def __init__(self, cam_data):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.cam_data = cam_data

        self.db=0
        self.chbEdgeLength = BOARD_SQUARE_LENGTH

        self.start=True
        self.tstart=0
        self.calib=False

        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        self.objp = np.zeros((6*9,3), np.float32)
        self.objp[:,:2] = np.mgrid[0:9,0:6].T.reshape(-1,2)*self.chbEdgeLength

        self.corners_all = []
        self.ids_all = []
        self.image_size = None

        self.not_loaded = True

    def calibrate(self, frame):
        if not self.calib:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            arucoDetector = cv2.aruco.ArucoDetector(dictionary=ARUCO_TYPE)
            charucoDetector = cv2.aruco.CharucoDetector(board)

            corners, ids, _ = arucoDetector.detectMarkers(gray)

            frame = cv2.aruco.drawDetectedMarkers(image=frame, corners=corners)
            charuco_corners, charuco_ids, _, _ = charucoDetector.detectBoard(frame)

            if not self.image_size:
                self.image_size = gray.shape[::-1]


        if self.db < 20:
            if charuco_ids is not None and len(charuco_ids) > 5 and self.start:
                self.start=False
                self.tstart=time.time()
                self.corners_all.append(charuco_corners)
                self.ids_all.append(charuco_ids)
            
                frame = cv2.aruco.drawDetectedCornersCharuco(frame, charucoCorners=charuco_corners, charucoIds=charuco_ids)
                self.db=self.db+1
            elif charuco_ids is not None and len(charuco_ids) > 5 and time.time()-self.tstart>0.5:
                self.tstart=time.time()
                self.corners_all.append(charuco_corners)
                self.ids_all.append(charuco_ids)

                frame = cv2.aruco.drawDetectedCornersCharuco(frame, charucoCorners=charuco_corners, charucoIds=charuco_ids)
                self.db=self.db+1
            else:
                if charuco_ids is not None and len(charuco_ids) > 5:
                    frame = cv2.aruco.drawDetectedCornersCharuco(frame, charucoCorners=charuco_corners, charucoIds=charuco_ids)
                else:                
                    cv2.putText(frame, "Please show chessboard.", (0,64), self.font, 1, (0,0,255),2,cv2.LINE_AA)
        else:
            if self.calib==False:
                self.calib=True
                ret, self.mtx, self.dist, self.rvecs, self.tvecs = cv2.aruco.calibrateCameraCharuco(charucoCorners=self.corners_all, 
                                                                                                       charucoIds=self.ids_all, 
                                                                                                       board=board, 
                                                                                                       imageSize=self.image_size, 
                                                                                                       cameraMatrix=None, 
                                                                                                       distCoeffs=None)
                h, w = frame.shape[:2]
                self.newcameramtx, self.roi=cv2.getOptimalNewCameraMatrix(self.mtx,self.dist,(w,h),1,(w,h))
                np.savez("./calibration_files/camcalib", ret=ret, mtx=self.mtx, dist=self.dist, rvecs=self.rvecs, tvecs=self.tvecs)
            
            frame = cv2.undistort(frame, self.mtx, self.dist, None, self.newcameramtx)
            x,y,w,h = self.roi
            frame = frame[y:y+h, x:x+w]
            cv2.putText(frame, "Camera calibrated.", (0,64), self.font, 1, (0,255,0),2,cv2.LINE_AA)

        return frame
    
    def detect(self, frame):
        if self.not_loaded:
            with np.load(self.cam_data) as X:
                self.mtx = X['mtx']
                self.dist = X['dist']
            self.not_loaded=False

        h, w = frame.shape[:2]
        newcameramtx, roi=cv2.getOptimalNewCameraMatrix(self.mtx,self.dist,(w,h),1,(w,h))

        frame = cv2.undistort(frame, self.mtx, self.dist, None, newcameramtx)

        x,y,w,h = roi
        frame = frame[y:y+h, x:x+w]

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        arucoDetector = cv2.aruco.ArucoDetector(dictionary=ARUCO_TYPE)
        corners, ids, _ = arucoDetector.detectMarkers(gray)

        id_list=[]
        rvecs = []
        tvecs = []

        if np.all(ids != None):
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, MARKER_LENGTH, self.mtx, self.dist)

            for i in range(0, ids.size):
                cv2.drawFrameAxes(frame, self.mtx, self.dist, rvecs[i], tvecs[i], 0.1)
                
                id_list.append(ids[i][0])

            cv2.aruco.drawDetectedMarkers(frame, corners, ids=ids)

        return frame, id_list, rvecs, tvecs, corners, w, h
