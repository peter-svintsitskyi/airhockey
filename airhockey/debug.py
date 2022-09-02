import logging

import cv2
import numpy as np
from airhockey.vision.color import ColorRange
import textwrap


class DebugWindowLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        msg = self.format(record)
        self.messages.append(msg)

    def draw(self, frame, y_start):
        if len(self.messages) > 3:
            self.messages.pop(0)
        line_num = 0
        for m in self.messages:
            for index, line in enumerate(textwrap.wrap(m, 90)):
                cv2.putText(frame, line,
                            (500, y_start + line_num * 40 - index * 15 + 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 255, 150),
                            thickness=2)
                line_num += 1


class DebugWindow(object):
    def __init__(self, *, name, log, translator, table_size,
                 color_ranges: list['ColorRange']):
        self.name = name
        self.translator = translator
        self.table_size = table_size
        self.color_ranges = color_ranges
        cv2.namedWindow(self.name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.name, 1000, 1000)
        # self.frame = None
        # self.hsv = None

        self.log_handler = DebugWindowLogHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        self.log_handler.setLevel(logging.INFO)
        logger = logging.getLogger(log)
        logger.addHandler(self.log_handler)

        for r in color_ranges:
            cv2.createTrackbar('{name} H Low'.format(name=r.name), self.name,
                               0, 179, r.set_h_low)
            cv2.setTrackbarPos('{name} H Low'.format(name=r.name), self.name,
                               r.h_low)
            cv2.createTrackbar('{name} H High'.format(name=r.name), self.name,
                               0, 179, r.set_h_high)
            cv2.setTrackbarPos('{name} H High'.format(name=r.name), self.name,
                               r.h_high)
            cv2.createTrackbar('{name} SV Low'.format(name=r.name), self.name,
                               0, 255, r.set_sv_low)
            cv2.setTrackbarPos('{name} SV Low'.format(name=r.name), self.name,
                               r.sv_low)

    def draw_color_previews(self, target, y_start):
        width = 200
        height = 50
        for index, r in enumerate(self.color_ranges):
            preview = np.zeros((height, width, 4), np.uint8)
            preview_hsv = np.zeros((preview.shape[0], preview.shape[1], 3), np.uint8)

            for row in range(0, height):
                sv = r.sv_low + (255 - r.sv_low) / height * row
                for col in range(0, width):
                    h = r.h_low + (r.h_high - r.h_low) / width * col
                    preview_hsv[row][col] = [h, sv, sv]
            preview[:, :, :3] = cv2.cvtColor(preview_hsv, cv2.COLOR_HSV2BGR)

            offset = (y_start + index * (height + 10), 0)
            target[offset[0]:offset[0] + preview.shape[0],
                   offset[1]:offset[1] + preview.shape[1]] = preview


    def set_frame(self, frame, hsv):
        self.frame = frame
        self.hsv = hsv

    def draw(self, queries: list):
        for query in queries:
            query.draw(self)
        cv2.rectangle(self.frame, self.translator.w2f((0, 0)),
                      self.translator.w2f(self.table_size),
                      (0, 255, 255), 2)
        h, w, d = self.frame.shape
        target = np.zeros((h + 300, w + 300, d), np.uint8)
        target[0:h, 0:w] = self.frame
        self.log_handler.draw(target, h)
        self.draw_color_previews(target, h)
        cv2.imshow(self.name, target)

        # for r in self.color_ranges:
        #     lower_color = np.array([r.h_low, r.sv_low, r.sv_low])
        #     upper_color = np.array([r.h_high, 255, 255])
        #     mask = cv2.inRange(self.hsv, lower_color, upper_color)
        #     cv2.imshow(r.name, mask)
        cv2.waitKey(1)

    def draw_circle(self, world_coordinates, color):
        hsv_color = np.uint8([[color]])
        bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
        bgr_color = (int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2]))
        bgr_color = (0, 0, 255)
        c = self.translator.w2f(world_coordinates)
        cv2.circle(self.frame, c, 10, bgr_color, -1)


class Debug(object):
    def __init__(self, translator, robot):
        self.translator = translator
        self.robot = robot

    def draw(self, *, frame, world_debug, robot_position, robot_dst, fps,
             video_stream):
        # table
        cv2.rectangle(frame, self.translator.w2f((0, 0)),
                      self.translator.w2f(world_debug['table_size']),
                      (0, 255, 255), 2)

        # trajectory
        for intersection in world_debug['trajectory']:
            point, velocity = intersection
            cv2.circle(frame, self.translator.w2f(point), 10, (0, 0, 255), -1)
            # cv2.putText(frame, str(velocity), translator.w2f(point),
            # cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 127, 255), thickness=3)

        # puck center
        if world_debug['puck_info'] is not None:
            cv2.circle(
                frame,
                self.translator.w2f(world_debug['puck_info'].position),
                10, (255, 0, 0), -1)

            # puck vector
            cX, cY = self.translator.w2f(world_debug['puck_info'].position)
            vX, vY = world_debug['puck_info'].vector
            # velocity = world_debug['puck_info'].velocity
            line_len = 200
            #             if velocity > 10:
            #                 line_len = velocity * 2
            cv2.line(frame, (cX, cY),
                     (int(cX + vX * line_len), int(cY + vY * line_len)),
                     (0, 255, 0), 7)

        # robot position
        if robot_position is not None:
            cv2.circle(frame, self.translator.w2f(robot_position), 10,
                       (255, 0, 255), -1)
            if self.robot.destination is not None:
                (rX, rY) = robot_position
                (rdX, rdY) = robot_dst
                cv2.line(frame, self.translator.w2f(robot_position),
                         self.translator.w2f((int(rdX), int(rdY))),
                         (0, 255, 0), 7)

        cv2.putText(frame, str("FPS: {0:.2f}".format(fps)), (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), thickness=3)
        cv2.putText(frame, str("Stream: {0}/{1:.2f} fps".format(
            video_stream.frames_grabbed, video_stream.stream_fps())), (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), thickness=3)
        cv2.putText(frame, str("Processed: {0}/{1:.2f} fps".format(
            video_stream.frames_read, video_stream.read_fps())), (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), thickness=3)
        # debug
        # cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('frame', 600, 600)
        cv2.imshow('frame', frame)
