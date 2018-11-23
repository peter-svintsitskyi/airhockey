import numpy as np
import cv2

color = np.uint8([[[0, 255, 255]]])
hsv_color = cv2.cvtColor(color, cv2.COLOR_BGR2HSV)

hsv_color = cv2.cvtColor(np.uint8([[[110, 100, 100]]]), cv2.COLOR_HSV2BGR)

print(hsv_color)

h_lower = 110
h_upper = 140

s_lower = 70
s_upper = 255

width = h_upper - h_lower
height = s_upper - s_lower

image = np.zeros((height, width, 3), np.uint8)
image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

for h in range(h_lower, h_upper):
    for s in range(s_lower, s_upper):
        bgr = cv2.cvtColor(np.uint8([[[h, s, s]]]), cv2.COLOR_HSV2BGR)
        image_hsv[s_upper - s - 1][h_upper - h - 1] = bgr[0][0]

cv2.imshow('image', image_hsv)

while True:
    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

