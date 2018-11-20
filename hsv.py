import cv2
import numpy as np

cap = cv2.VideoCapture(0)

while(1):

    # Take each frame
    _, frame = cap.read()

    # Convert BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # define range of blue color in HSV
    lower_blue = np.array([25,50,50])
    upper_blue = np.array([35,255,255])

    # Threshold the HSV image to get only blue colors
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    erosion_size = 2
    element = cv2.getStructuringElement(cv2.MORPH_RECT, (2*erosion_size + 1, 2*erosion_size+1), (erosion_size, erosion_size))
    eroded = cv2.erode(mask, element)

    dilation_size = 3
    dilation_element = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * dilation_size + 1, 2 * dilation_size + 1), (dilation_size, dilation_size))
    dilated = cv2.dilate(eroded, dilation_element)

    _, contours, hierarchy = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours):
        biggest_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(biggest_contour)
        cX = int(M["m10"] / (M["m00"] + 0.00001))
        cY = int(M["m01"] / (M["m00"] + 0.00001))
        # print(m)
        cv2.circle(frame, (cX, cY), 10, (255, 0, 0), -1)

        cv2.drawContours(frame, [biggest_contour], -1, (0, 255, 0), 3)

    # Bitwise-AND mask and original image
    res = cv2.bitwise_and(frame, frame, mask=dilated)

    cv2.imshow('frame',frame)
    # cv2.imshow('mask',mask)
    # cv2.imshow('eroded', eroded)
    # cv2.imshow('dilated', dilated)
    # cv2.imshow('res',res)
    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

cv2.destroyAllWindows()

