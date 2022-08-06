import time


class FrameThrottler(object):
    def __init__(self, desired_fps):
        self.desired_fps = desired_fps
        self.last_frame_time = None
        self.fps = 0
        self.start = time.time()
        self.number_of_frames = 0

    def throttle(self):
        if self.last_frame_time is None:
            self.last_frame_time = time.time()

        self.number_of_frames += 1

        diff = time.time() - self.last_frame_time
        if diff < 1 / self.desired_fps:
            time.sleep(1 / self.desired_fps - diff)

        self.last_frame_time = time.time()

        self.fps = self.number_of_frames / (self.last_frame_time - self.start)
