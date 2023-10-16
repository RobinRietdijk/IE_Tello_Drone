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
        self.camera = cv2.VideoCapture(0)

        # Drone velocities between -100~100
        self.for_back_velocity = 0
        self.left_right_velocity = 0
        self.up_down_velocity = 0
        self.yaw_velocity = 0
        self.speed = 10
        
        # Variables for drone's states
        self.battery = 0
        self.angles = [0., 0., 0., 0.]

        # Bool variables for setting functions
        self.send_rc_control = False
        self.save = False
        self.aruco_detection = False

        self.calibrate = False

        self.navigate_event = threading.Event()
        self.navigate_event.clear()

        self.dir_queue = queue.Queue()
        self.dir_queue.queue.clear()

        self.arucoNav = arucoController(15, self.dir_queue, self.navigate_event)

        # Create update timer
        pygame.time.set_timer(USEREVENT + 1, 1000 // FPS)

    def run(self):
        directions = np.zeros(4)

        time.sleep(3)

        should_stop = False
        while not should_stop:
            s, img = self.camera.read()
            frame=cv2.resize(img, (960,720))
            for event in pygame.event.get():
                if event.type == QUIT:
                    should_stop = True
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        should_stop = True
                    else:
                        self.keydown(event.key)
                elif event.type == KEYUP:
                    self.keyup(event.key)
            
            frame = self.arucoNav.detect(frame)

            self.screen.fill([0, 0, 0])

            frame=cv2.resize(frame, (640,480))

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = np.flipud(frame)

            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(frame, (0, 0))
            pygame.display.update()

            time.sleep(1 / FPS)

    def keydown(self, key):
        pass

    def keyup(self, key):
        if key == pygame.K_o: # Toggle aruco detection
            if self.aruco_detection:
                self.aruco_detection = False
            else:
                self.aruco_detection = True
        if key == pygame.K_p: # Toggle nav enent
            if self.navigate_event.is_set():
                self.navigate_event.clear()
            else:
                self.navigate_event.set()
    
def main() -> None:
    frontend = FrontEnd()
    frontend.run()

if __name__ == "__main__":
    main()