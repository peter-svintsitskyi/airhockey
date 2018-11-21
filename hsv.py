import cv2
import numpy as np
from sklearn import preprocessing
import math

class Tracker(object):
    x = None
    y = None
    old_vector = None

    def direction(self, x, y):
        if self.x is None:
            self.x = x
            self.y = y
            return None

        dx = x - self.x
        dy = y - self.y

        velocity_square = dx*dx + dy*dy

        vector = preprocessing.normalize(
            np.asarray([dx, dy]).reshape(1, -1)
        )

        if velocity_square > 100:
            self.old_vector = vector[0]
            self.x = x
            self.y = y

        if self.old_vector is None:
            return None

        return self.old_vector, math.sqrt(velocity_square)


def detect_puck_position(frame):
    # Convert BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # define range of blue color in HSV
    lower_color = np.array([25, 50, 50])
    upper_color = np.array([35, 255, 255])
    # Threshold the HSV image to get only blue colors
    mask = cv2.inRange(hsv, lower_color, upper_color)
    erosion_size = 2
    element = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * erosion_size + 1, 2 * erosion_size + 1),
                                        (erosion_size, erosion_size))
    eroded = cv2.erode(mask, element)
    dilation_size = 3
    dilation_element = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * dilation_size + 1, 2 * dilation_size + 1),
                                                 (dilation_size, dilation_size))
    dilated = cv2.dilate(eroded, dilation_element)
    # Bitwise-AND mask and original image
    # res = cv2.bitwise_and(frame, frame, mask=dilated)
    # cv2.imshow('mask',mask)
    # cv2.imshow('eroded', eroded)
    # cv2.imshow('dilated', dilated)
    # cv2.imshow('res',res)

    _, contours, __ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours):
        biggest_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(biggest_contour)
        cX = int(M["m10"] / (M["m00"] + 0.00001))
        cY = int(M["m01"] / (M["m00"] + 0.00001))
        # print(m)

        return (cX, cY), biggest_contour

    return (None, None), None


cap = cv2.VideoCapture(0)

tracker = Tracker()

while(1):

    # Take each frame
    _, frame = cap.read()

    (cX, cY), biggest_contour = detect_puck_position(frame)

    if biggest_contour is not None:
        cv2.circle(frame, (cX, cY), 10, (255, 0, 0), -1)

        track = tracker.direction(cX, cY)

        if track is not None:
            (vX, vY), velocity = track
            line_len = 0

            if velocity > 10:
                line_len = velocity * 2

            cv2.line(frame, (cX, cY), (int(cX + vX * line_len), int(cY + vY * line_len)), (0, 255, 0), 7)

    cv2.imshow('frame', frame)
    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

cv2.destroyAllWindows()

