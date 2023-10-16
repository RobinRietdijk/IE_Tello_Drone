import path
import sys

import cv2
import configparser
import numpy as np
from aruco_dict import ARUCO_DICT

directory = path.Path(__file__).abspath()
sys.path.append(directory.parent.parent.parent)

from config import CONFIG

ARUCO_TYPE = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[CONFIG['Aruco']['type']])
BOARD_COLS = CONFIG['Aruco']['board_cols']
BOARD_ROWS = CONFIG['Aruco']['board_rows']
BOARD_HEIGHT = CONFIG['Aruco']['board_height']
BOARD_WIDTH = CONFIG['Aruco']['board_width']
BOARD_SQUARE_LENGTH = CONFIG['Aruco']['board_square_length']
BOARD_MARKER_LENGTH = CONFIG['Aruco']['board_marker_length']

board = cv2.aruco.CharucoBoard((BOARD_COLS, BOARD_ROWS), BOARD_SQUARE_LENGTH, BOARD_MARKER_LENGTH, ARUCO_TYPE)

def generate_board():
    img = np.zeros((BOARD_WIDTH, BOARD_HEIGHT, 1), dtype="uint8")
    board.generateImage((BOARD_WIDTH, BOARD_HEIGHT), img, 10, 1)
    cv2.imwrite("BoardImage.jpg", img)

generate_board()
img = cv2.imread('BoardImage.jpg')