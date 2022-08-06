import cv2
import numpy as np


class ColorRange(object):
    def __init__(self, *, name: str, h_low, h_high, sv_low):
        self.name = name
        self.sv_low = sv_low
        self.h_high = h_high
        self.h_low = h_low

    def set_h_low(self, v):
        self.h_low = v

    def set_h_high(self, v):
        self.h_high = v

    def set_sv_low(self, v):
        self.sv_low = v

    def __eq__(self, other):
        return self.h_low == other.h_low and self.h_high == other.h_high and \
               self.sv_low == other.sv_low

    def __repr__(self):
        return "ColorRange(H=({h_low},{h_high};SV_LOW={sv_low})".format(
            h_low=self.h_low,
            h_high=self.h_high,
            sv_low=self.sv_low)


class ColorDetector(object):
    def __init__(self, *, color_range: ColorRange, translator):
        self.color_range = color_range
        self.translator = translator

    def get_positions(self, hsv, number_of_results, frame) -> list:
        lower_color = np.array([self.color_range.h_low,
                                self.color_range.sv_low,
                                self.color_range.sv_low])
        upper_color = np.array([self.color_range.h_high, 255, 255])
        mask = cv2.inRange(hsv, lower_color, upper_color)
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST,
                                       cv2.CHAIN_APPROX_SIMPLE)
        areas = []
        for i, c in enumerate(contours):
            area = cv2.contourArea(c)
            areas.append(area)

        sorted_contours = sorted(zip(areas, contours), key=lambda x: x[0],
                                 reverse=True)

        result = []
        for i in range(number_of_results):
            if i == len(sorted_contours):
                break

            M = cv2.moments(sorted_contours[i][1])
            cX = int(M["m10"] / (M["m00"] + 0.00001))
            cY = int(M["m01"] / (M["m00"] + 0.00001))
            result.append(self.translator.f2w((cX, cY)))

        return result
