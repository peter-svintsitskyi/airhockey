import cv2
import time
from threading import Thread, Lock
import numpy as np


class VideoStream(object):
    def __init__(self, path, frame_dimensions):
        frame_width, frame_height = frame_dimensions
        self.stream = cv2.VideoCapture(path)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        self.stream.set(cv2.CAP_PROP_FPS, 30)
        self.stopped = False
        self.frame = None
        self.frames_grabbed = 0
        self.frames_read = 0
        self.time_started = time.time()
        self.read_lock = Lock()

    def get_real_frame_size(self):
        return self.stream.get(cv2.CAP_PROP_FRAME_WIDTH), self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def start(self):
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return

            grabbed, frame = self.stream.read()

            with self.read_lock:
                self.frame = frame

            self.frames_grabbed += 1

    def read(self):
        with self.read_lock:
            frame = self.frame.copy()

        self.frames_read += 1

        return frame

    def has_frame(self):
        # return True if there are still frames in the queue
        return self.frame is not None

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

    def stream_fps(self):
        return self.frames_grabbed / (time.time() - self.time_started)

    def read_fps(self):
        return self.frames_read / (time.time() - self.time_started)



class VideoStream1(object):
    def __init__(self, path, frame_dimensions):
        frame_width, frame_height = frame_dimensions
        self.stream = cv2.VideoCapture(path)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        self.stream.set(cv2.CAP_PROP_FPS, 90)
        self.stopped = False
        self.frames_grabbed = 0
        self.frames_read = 0
        self.time_started = time.time()
        self.has_grabbed_frame = False

    def get_real_frame_size(self):
        return self.stream.get(cv2.CAP_PROP_FRAME_WIDTH), self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def start(self):
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return

            self.has_grabbed_frame = self.stream.grab()
            if self.has_grabbed_frame:
                self.frames_grabbed += 1

    def read(self):
        ok, frame = self.stream.retrieve()
        self.frames_read += 1
        return frame

    def has_frame(self):
        # return True if there are still frames in the queue
        return self.has_grabbed_frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

    def stream_fps(self):
        return self.frames_grabbed / (time.time() - self.time_started)

    def read_fps(self):
        return self.frames_read / (time.time() - self.time_started)



video_stream = VideoStream(0, (640, 480))
frame_size = video_stream.get_real_frame_size()
print('camera resolution {w}:{h}'.format(w=frame_size[0], h=frame_size[1]))

video_stream.start()

while not video_stream.has_frame():
    print('awaiting frame')
    time.sleep(1)

while video_stream.has_frame():
    frame = video_stream.read()
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_color = np.array([90, 50, 50])
    upper_color = np.array([110, 255, 255])

    mask = cv2.inRange(hsv, lower_color, upper_color)

    cv2.putText(frame,
                str("FPS: {0}/{1} S {2:.2f} R {3:.2f}".format(video_stream.frames_grabbed, video_stream.frames_read, video_stream.stream_fps(), video_stream.read_fps())),
                (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), thickness=3)

    
    
    _, contours, __ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours):
        biggest_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(biggest_contour)
        cX = int(M["m10"] / (M["m00"] + 0.00001))
        cY = int(M["m01"] / (M["m00"] + 0.00001))
        cv2.circle(
                frame,
                (cX, cY),
                10, (255, 0, 0), -1)

    cv2.imshow('frame', frame)


    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break