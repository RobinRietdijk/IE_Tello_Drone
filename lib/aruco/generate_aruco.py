import path
import sys

import numpy as np
import cv2
from aruco_dict import ARUCO_DICT

directory = path.Path(__file__).abspath()
sys.path.append(directory.parent.parent.parent)

from config import CONFIG

for id in range(1, CONFIG['Aruco']['num_markers']):

    arucoDict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[CONFIG['Aruco']['type']])

    print(f"ArUCo type '{id}' with ID '{id}'".format(CONFIG['Aruco']['type']))
    tag = np.zeros((CONFIG['Aruco']['tag_size'], CONFIG['Aruco']['tag_size'], 1), dtype="uint8")
    cv2.aruco.generateImageMarker(arucoDict, id, CONFIG['Aruco']['tag_size'], tag, 1)

    tag_name = "./aruco_markers/" + CONFIG['Aruco']['type'] + "_" + str(id) + ".png"
    cv2.imwrite(tag_name, tag)