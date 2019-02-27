import cv2
import numpy as np
from sklearn import preprocessing
import math
import time
import socket
import json
from random import randint
from threading import Thread, Lock


def get_intersect(a1, a2, b1, b2):
    """ 
    Returns the point of intersection of the lines passing through a2,a1 and b2,b1.
    a1: [x, y] a point on the first line
    a2: [x, y] another point on the first line
    b1: [x, y] a point on the second line
    b2: [x, y] another point on the second line
    """

    s = np.vstack([a1, a2, b1, b2])  # s for stacked
    h = np.hstack((s, np.ones((4, 1))))  # h for homogeneous
    l1 = np.cross(h[0], h[1])  # get first line
    l2 = np.cross(h[2], h[3])  # get second line
    x, y, z = np.cross(l1, l2)  # point of intersection
    if z == 0:  # lines are parallel
        return (float('inf'), float('inf'))

    return (x / z, y / z)


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

        velocity_square = dx * dx + dy * dy

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


class WorldToFrameTranslator(object):
    def __init__(self, frame_size, table_size):
        self.frame_width, self.frame_height = frame_size
        self.table_width, self.table_height = table_size
        self.horizontal_margin = 10
        frame_field_width = self.frame_width - self.horizontal_margin * 2
        frame_field_height = frame_field_width / 2
        self.vertical_margin = (self.frame_height - frame_field_height) / 2

        self.horizontal_ratio = self.table_width / frame_field_width
        self.vertical_ratio = self.table_height / frame_field_height

    def w2f(self, point):
        pX, pY = point

        return int(pX / self.horizontal_ratio + self.horizontal_margin), int(
            pY / self.vertical_ratio + self.vertical_margin)

    def f2w(self, point):
        pX, pY = point

        return int((pX - self.horizontal_margin) * self.horizontal_ratio), int(
            (pY - self.vertical_margin) * self.vertical_ratio)


class ColorDetector(object):
    def __init__(self, *, h_low, h_high, sv_low):
        self.h_low = h_low
        self.h_high = h_high
        self.sv_low = sv_low

    def set_h_low(self, v):
        self.h_low = v

    def set_h_high(self, v):
        self.h_high = v

    def set_sv_low(self, v):
        self.sv_low = v


    def get_position(self, hsv):
        # define range of blue color in HSV
        lower_color = np.array([self.h_low, self.sv_low, self.sv_low])
        upper_color = np.array([self.h_high, 255, 255])

        # Threshold the HSV image to get only blue colors
        mask = cv2.inRange(hsv, lower_color, upper_color)

        _, contours, __ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours):
            biggest_contour = max(contours, key=cv2.contourArea)
            M = cv2.moments(biggest_contour)
            cX = int(M["m10"] / (M["m00"] + 0.00001))
            cY = int(M["m01"] / (M["m00"] + 0.00001))
            return (cX, cY)
            
        return None


class PuckInfo(object):
    def __init__(self, position, vector, velocity):
        self.vector = vector
        self.velocity = velocity
        self.position = position


class Robot(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.last_delta = None

    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()

    def delta(self, delta):
        x, y = delta
        self.last_delta = delta
        self.sock.sendto(bytes('{{"x":{x},"y":{y}}}\n'.format(x=x, y=y), "utf-8"), (self.host, self.port))
        

class GameStrategy(object):
    def __init__(self, world, robot):
        self.world = world
        self.robot = robot
        
        self.old_x = None
        self.old_y = None

    def tick(self, *, robot_position):
        if robot_position is None:
            return
            
        if self.world.puck_info is None:
            return
            
        # if len(self.world.trajectory) == 0:
        #    return

        # index = randint(0, len(self.world.trajectory) - 1)

        # point, eta = self.world.trajectory[index]
        
        cx, cy = robot_position
        
        puck_x, puck_y = world.puck_info.position
        
        if puck_x < 600 or puck_x > 1200 or puck_y < 0 or puck_y > 600:
            print("puck is out of field | PX = {px}, PY = {py}".format(px=puck_x, py=puck_y))
            return   
        
        # if cx == self.old_x and cy == self.old_y and self.move:
        #    self.move = False
            
        #    print("robot finished move")
        #    return
        
        if cx < 0 or cx > 600 or cy < 0 or cy > 600:
            print("robot current position is out of field")            
            return
                     
        # e = 10   
        # nx = randint(45 + e, 555 - e)
        # ny = randint(45 + e, 555 - e)
        
        nx = 1200 - puck_x
        ny = puck_y


        dx = nx - cx
        dy = ny - cy
        
        delta_limit = 10
        #print("X = {cx} + {dx} = {nx}; Y = {cy} + {dy} = {ny} | PX = {px}, PY = {py}".format(cx=cx, dx=dx, cy=cy, dy=dy, nx=nx, ny=ny, px=puck_x, py=puck_y))
        if abs(dx) < delta_limit and abs(dy) < delta_limit:
            print("delta too small")
            return
        
        self.old_x = cx
        self.old_y = cy
        
        
        
        self.robot.delta((dx, dy))
        self.move = True
        
        

class World(object):
    def __init__(self, table_size):
        self.puck_info = None
        self.table_width, self.table_height = table_size
        self.table_size = table_size
        self.trajectory = []

    def tick(self, puck_info):
        self.puck_info = puck_info
        self.calculate_puck_trajectory()

    def calculate_puck_trajectory(self):
        self.trajectory = []

        if self.puck_info.vector[0] > 0:
            return

        for x in range(0, int(self.puck_info.position[0] / 2), 100):
            intersection = self.intersect_puck_trajectory_at_x(x)
            if intersection is not None:
                self.trajectory.append(intersection)

    def intersect_puck_trajectory_at_x(self, x):
        p_x, p_y = self.puck_info.position
        v_x, v_y = self.puck_info.vector
        intersection = get_intersect(
            (x, 0), (x, 1),
            self.puck_info.position, (p_x + v_x, p_y + v_y)
        )
        i_x, i_y = intersection

        if i_x == float('inf'):
            return None

        d_x = i_x - p_x
        d_y = i_y - p_y

        distance = math.sqrt(d_x * d_x + d_y * d_y)

        if self.puck_info.velocity != 0:
            time = distance / self.puck_info.velocity
        else:
            time = float('inf')

        n = int(i_y / self.table_height)
        if i_y < 0 or i_y > self.table_height:
            i_y = abs(i_y) - abs(n * self.table_height)

            if n % 2 != 0:
                i_y = self.table_height - i_y

        return (i_x, i_y), time

    def get_debug(self):
        return dict(
            puck_info=self.puck_info,
            table_size=self.table_size,
            trajectory=self.trajectory
        )


class Debug(object):
    def __init__(self, translator):
        self.translator = translator

    def draw(self, *, frame, world_debug, robot_position, robot_delta, fps, video_stream):
        # table
        cv2.rectangle(frame, translator.w2f((0, 0)), translator.w2f(world_debug['table_size']), (0, 255, 255), 2)

        # trajectory
        for intersection in world_debug['trajectory']:
            point, velocity = intersection
            cv2.circle(frame, translator.w2f(point), 10, (0, 0, 255), -1)
            # cv2.putText(frame, str(velocity), translator.w2f(point), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 127, 255), thickness=3)

        # puck center
        if world_debug['puck_info'] is not None:
            cv2.circle(
                frame,
                self.translator.w2f(world_debug['puck_info'].position),
                10, (255, 0, 0), -1)

            # puck vector
            cX, cY = self.translator.w2f(world_debug['puck_info'].position)
            vX, vY = world_debug['puck_info'].vector
            velocity = world_debug['puck_info'].velocity
            line_len = 0
            if velocity > 10:
                line_len = velocity * 2
            cv2.line(frame, (cX, cY), (int(cX + vX * line_len), int(cY + vY * line_len)), (0, 255, 0), 7)

        # robot position
        if robot_position is not None:
            cv2.circle(frame, self.translator.w2f(robot_position), 10, (255, 0, 255), -1)
            if robot_delta is not None:
                (rX, rY) = robot_position
                (dX, dY) = robot_delta
                rdX = rX + dX
                rdY = rY + dY             
                cv2.line(frame, self.translator.w2f(robot_position), self.translator.w2f((int(rdX), int(rdY))), (0, 255, 0), 7) 

        cv2.putText(frame, str("FPS: {0:.2f}".format(fps)), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), thickness=3)
        cv2.putText(frame, str("Stream: {0}/{1:.2f} fps".format(video_stream.frames_grabbed, video_stream.stream_fps())), (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), thickness=3)
        cv2.putText(frame, str("Processed: {0}/{1:.2f} fps".format(video_stream.frames_read, video_stream.read_fps())), (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), thickness=3)
        # debug
        #cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('frame', 600, 600)
        cv2.imshow('frame', frame)


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


class VideoStream(object):
    def __init__(self, path, frame_dimensions):
        frame_width, frame_height = frame_dimensions
        self.stream = cv2.VideoCapture(path)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        self.stream.set(cv2.CAP_PROP_FPS, 30)
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


if __name__ == '__main__':

    PUCK_H_LOW = 90
    PUCK_H_HIGH = 110
    PUCK_SV_LOW = 50
    puck_detector = ColorDetector(h_low=PUCK_H_LOW, h_high=PUCK_H_HIGH, sv_low=PUCK_SV_LOW)

    ROBOT_H_LOW = 20
    ROBOT_H_HIGH = 30
    ROBOT_SV_LOW = 125
    robot_detector = ColorDetector(h_low=ROBOT_H_LOW, h_high=ROBOT_H_HIGH, sv_low=ROBOT_SV_LOW)

    cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
    cv2.createTrackbar('Puck H Low', 'frame', 0, 255, lambda x: puck_detector.set_h_low(x))
    cv2.setTrackbarPos('Puck H Low', 'frame', PUCK_H_LOW)
    cv2.createTrackbar('Puck H High', 'frame', 0, 255, lambda x: puck_detector.set_h_high(x))
    cv2.setTrackbarPos('Puck H High', 'frame', PUCK_H_HIGH)
    cv2.createTrackbar('Puck SV Low', 'frame', 0, 255, lambda x: puck_detector.set_sv_low(x))
    cv2.setTrackbarPos('Puck SV Low', 'frame', PUCK_SV_LOW)

    cv2.createTrackbar('Robot H Low', 'frame', 0, 255, lambda x: robot_detector.set_h_low(x))
    cv2.setTrackbarPos('Robot H Low', 'frame', ROBOT_H_LOW)
    cv2.createTrackbar('Robot H High', 'frame', 0, 255, lambda x: robot_detector.set_h_high(x))
    cv2.setTrackbarPos('Robot H High', 'frame', ROBOT_H_HIGH)
    cv2.createTrackbar('Robot SV Low', 'frame', 0, 255, lambda x: robot_detector.set_sv_low(x))
    cv2.setTrackbarPos('Robot SV Low', 'frame', ROBOT_SV_LOW)

    table_size = (1200, 600)
    video_stream = VideoStream(0, (640, 480))
    frame_size = video_stream.get_real_frame_size()
    print('camera resolution {w}:{h}'.format(w=frame_size[0], h=frame_size[1]))

    translator = WorldToFrameTranslator(frame_size, table_size)

    tracker = Tracker()
    world = World(table_size)
    debug = Debug(translator)

    video_stream.start()

    while not video_stream.has_frame():
        time.sleep(0.1)

    # frame_throttler = FrameThrottler(desired_fps=500)
    with Robot("192.168.44.45", 8888) as robot:

        game_strategy = GameStrategy(world, robot)

        while video_stream.has_frame():
            # frame_throttler.throttle()
            frame = video_stream.read()
            
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)            
            
            puck_position = puck_detector.get_position(hsv)

            if puck_position is not None:
                puck_position = translator.f2w(puck_position)
                track = tracker.direction(*puck_position)
                if track is not None:
                    vector, velocity = track
                    world.tick(PuckInfo(puck_position, vector, velocity))

            else:
                print('Puck not found')


            robot_position = robot_detector.get_position(hsv)
            if robot_position is not None:
                robot_position = translator.f2w(robot_position)

            debug.draw(frame=frame.copy(), world_debug=world.get_debug(),
                       robot_position=robot_position,
                       robot_delta=robot.last_delta,
                       fps=0,
                       video_stream=video_stream)

            game_strategy.tick(robot_position=robot_position)

            #if puck_detector.mask is not None:
            #    cv2.imshow('puck mask', puck_detector.mask)
            
            #if robot_detector.mask is not None:
            #    cv2.imshow('robot mask', robot_detector.mask)

            k = cv2.waitKey(5) & 0xFF
            if k == 27:
                break

    # print(frame_throttler.fps)

    cv2.destroyAllWindows()
    video_stream.stop()
