import time
import datetime
import pygame
import queue
import threading
import cv2
import numpy as np
from lib.graph import Graph
from lib.djitellopy import Tello
from video_writer import WriteVideo
from lib.aruco import Controller as arucoController
from pygame.locals import *

S = 60
FPS = 120

from config import CONFIG
from lib.aruco.aruco_dict import ARUCO_DICT

ARUCO_TYPE = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[CONFIG['Aruco']['type']])
BOARD_COLS = CONFIG['Aruco']['board_cols']
BOARD_ROWS = CONFIG['Aruco']['board_rows']
BOARD_HEIGHT = CONFIG['Aruco']['board_height']
BOARD_WIDTH = CONFIG['Aruco']['board_width']
BOARD_SQUARE_LENGTH = CONFIG['Aruco']['board_square_length']
BOARD_MARKER_LENGTH = CONFIG['Aruco']['board_marker_length']

S_PROG = CONFIG['Camera']['s_prog']

board = cv2.aruco.CharucoBoard((BOARD_ROWS, BOARD_COLS), BOARD_SQUARE_LENGTH, BOARD_MARKER_LENGTH, ARUCO_TYPE)

class FrontEnd(object):
    """ Maintains the Tello display and moves it through the keyboard keys.
        Press escape key to quit.
        The controls are:
            - T: Takeoff
            - L: Land
            - Arrow keys: Forward, backward, left and right.
            - A and D: Counter clockwise and clockwise rotations
            - W and S: Up and down.
    """

    def __init__(self):
        # Init pygame
        pygame.init()

        # Creat pygame window
        pygame.display.set_caption("Tello video stream")
        self.width = 640
        self.height = 480
        self.screen = pygame.display.set_mode([self.width, self.height])


        # Init Tello object that interacts with the Tello drone
        self.tello = Tello()

        # Drone velocities between -100~100
        self.for_back_velocity = 0
        self.left_right_velocity = 0
        self.up_down_velocity = 0
        self.yaw_velocity = 0
        self.speed = 10
        
        # Variables for drone's states
        self.battery = 0
        self.angles = [0., 0., 0., 0.]

        self.dir_queue = queue.Queue()
        self.dir_queue.queue.clear()

        # Bool variables for setting functions
        self.send_rc_control = False
        self.save = False
        self.aruco_detection = False

        self.calibrate = False

        self.navigate_event = threading.Event()
        self.navigate_event.clear()

        self.arucoNav = arucoController(S_PROG, self.dir_queue, self.navigate_event)

        # Create update timer
        pygame.time.set_timer(USEREVENT + 1, 1000 // FPS)

    def run(self):

        self.tello.connect()
        self.tello.set_speed(self.speed)

        self.tello.streamoff()
        self.tello.streamon()

        frame_read = self.tello.get_frame_read()
        directions = np.zeros(4)

        time.sleep(3)

        should_stop = False
        while not should_stop:
            frame=cv2.resize(frame_read.frame, (960,720))
            for event in pygame.event.get():
                if event.type == USEREVENT + 1:
                    self.update(directions)
                elif event.type == QUIT:
                    should_stop = True
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        should_stop = True
                    else:
                        self.keydown(event.key)
                elif event.type == KEYUP:
                    self.keyup(event.key)

            if frame_read.stopped:
                frame_read.stop()
                break

            # Save image on 'M' press
            if self.save:
                timestr = time.strftime("%Y%m%d_%H%M%S")
                cv2.imwrite("./images/"+timestr+".jpg", frame)
                self.save = False

            if self.calibrate:
                self.arucoNav.calibrate(frame)
            
            frame = self.arucoNav.detect(frame)

            self.screen.fill([0, 0, 0])

            text = "Battery: {}%".format(self.tello.get_battery())
            cv2.putText(frame, text, (5, 720 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            frame=cv2.resize(frame, (640,480))

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = np.flipud(frame)

            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(frame, (0, 0))
            pygame.display.update()

            time.sleep(1 / FPS)

        self.tello.end()

    def keydown(self, key):
        """ Update velocities based on key pressed
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP:  # set forward velocity
            self.for_back_velocity = S
        elif key == pygame.K_DOWN:  # set backward velocity
            self.for_back_velocity = -S
        elif key == pygame.K_LEFT:  # set left velocity
            self.left_right_velocity = -S
        elif key == pygame.K_RIGHT:  # set right velocity
            self.left_right_velocity = S
        elif key == pygame.K_w:  # set up velocity
            self.up_down_velocity = S
        elif key == pygame.K_s:  # set down velocity
            self.up_down_velocity = -S
        elif key == pygame.K_a:  # set yaw clockwise velocity
            self.yaw_velocity = -S
        elif key == pygame.K_d:  # set yaw counter clockwise velocity
            self.yaw_velocity = S

    def keyup(self, key):
        """ Update velocities based on key released
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP or key == pygame.K_DOWN:  # set zero forward/backward velocity
            self.for_back_velocity = 0
        elif key == pygame.K_LEFT or key == pygame.K_RIGHT:  # set zero left/right velocity
            self.left_right_velocity = 0
        elif key == pygame.K_w or key == pygame.K_s:  # set zero up/down velocity
            self.up_down_velocity = 0
        elif key == pygame.K_a or key == pygame.K_d:  # set zero yaw velocity
            self.yaw_velocity = 0
        elif key == pygame.K_t:  # takeoff
            self.tello.takeoff()
            self.send_rc_control = True
        elif key == pygame.K_l:  # land
            self.tello.land()
            self.send_rc_control = False
        elif key == pygame.K_k: # camera calibration
            if self.calibrate:
                self.calibrate = False
            else:
                self.calibrate = True
        elif key == pygame.K_o:  # start navigation
            if self.navigate_event.is_set():
                self.navigate_event.clear()
            else:
                self.navigate_event.set()
        elif key == pygame.K_m:  # save image
            self.save = True

    def update(self):
        """ Update routine. Send velocities to Tello."""
        if self.send_rc_control:
            if self.navigate_event.is_set() and not self.dir_queue.empty():
                x, y, z, yaw = self.dir_queue.get()
                self.tello.send_rc_control(int(x), int(y), int(z), int(yaw))
            else:
                self.dir_queue.queue.clear()
                self.tello.send_rc_control(self.left_right_velocity, self.for_back_velocity, self.up_down_velocity,
                                        self.yaw_velocity)
    
def main() -> None:
    frontend = FrontEnd()
    frontend.run()

if __name__ == "__main__":
    main()