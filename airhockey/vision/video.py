import cv2
import time
from threading import Thread, Lock
import numpy as np
from mss import mss
import abc


class FrameReader(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def read(self): raise NotImplementedError


class VideoStream(FrameReader):
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
        self.has_grabbed_frame = False
        self.read_lock = Lock()
        self.has_new_frame = False

    def start(self):
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        self.time_started = time.time()
        return self

    def update(self):
        while True:
            if self.stopped:
                return

            self.has_grabbed_frame, frame = self.stream.read()

            with self.read_lock:
                self.has_new_frame = True
                self.frame = frame

            self.frames_grabbed += 1

    def read(self):

        with self.read_lock:
            if self.has_new_frame:
                self.frames_read += 1
            frame = self.frame.copy()
            self.has_new_frame = False

        return frame

    def has_frame(self):
        return self.has_grabbed_frame

    def stop(self):
        self.stopped = True

    def stream_fps(self):
        return self.frames_grabbed / (time.time() - self.time_started)

    def read_fps(self):
        return self.frames_read / (time.time() - self.time_started)


class ScreenCapture(FrameReader):
    def __init__(self, frame_dimensions):
        width, height = frame_dimensions
        self.bounding_box = {'top': 150, 'left': 100, 'width': width / 2,
                             'height': height / 2}
        self.sct = mss()
        self.stopped = False
        self.frame = None
        self.frames_grabbed = 0
        self.frames_read = 0
        self.time_started = time.time()
        self.has_grabbed_frame = False
        self.read_lock = Lock()
        self.has_new_frame = False

    def start(self):
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        self.time_started = time.time()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            sct_img = self.sct.grab(self.bounding_box)
            frame = np.array(sct_img)
            self.has_grabbed_frame = True

            with self.read_lock:
                self.has_new_frame = True
                self.frame = frame

            self.frames_grabbed += 1

    def read(self):

        with self.read_lock:
            if self.has_new_frame:
                self.frames_read += 1
            frame = self.frame.copy()
            self.has_new_frame = False

        return frame

    def has_frame(self):
        return self.has_grabbed_frame

    def stop(self):
        self.stopped = True

    def stream_fps(self):
        return self.frames_grabbed / (time.time() - self.time_started)

    def read_fps(self):
        return self.frames_read / (time.time() - self.time_started)
