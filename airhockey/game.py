import cv2
import numpy as np
from sklearn import preprocessing
import math
import time
import socket
import json

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

        return int(pX * self.horizontal_ratio - self.horizontal_margin), int(
            pY * self.vertical_ratio - self.vertical_margin)


def detect_puck_position(frame):
    # Convert BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # define range of blue color in HSV
    lower_color = np.array([100, 100, 100])
    upper_color = np.array([140, 255, 255])
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

        return cX, cY

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

    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()

    def get_position(self):
        self.sock.sendall(bytes("{}\n", "utf-8"))
        received = str(self.sock.recv(1024), "utf-8")
        return json.loads(received)

    def move_to(self, point):
        x, y = point
        self.sock.sendall(bytes('\{"x":{x},"y":{y}\}\n'.format(x=x, y=y), "utf-8"))
        received = str(self.sock.recv(1024), "utf-8")
        return json.loads(received)


class GameStrategy(object):
    pass


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
        for x in range(0, int(self.table_width / 2), 5):
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

    def draw(self, frame, world_debug, fps):
        # table
        cv2.rectangle(frame, translator.w2f((0, 0)), translator.w2f(world_debug['table_size']), (0, 255, 255), 2)

        # trajectory
        for intersection in world_debug['trajectory']:
            point, velocity = intersection
            cv2.circle(frame, translator.w2f(point), 10, (0, 0, 255), -1)
            # cv2.putText(frame, str(velocity), translator.w2f(point), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 127, 255), thickness=3)

        # puck center
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

        cv2.putText(frame, str("FPS: {0}".format(fps)), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (160, 127, 235),
                    thickness=3)
        # debug
        cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
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


if __name__ == '__main__':

    table_size = (1200, 600)

    cap = cv2.VideoCapture(0)

    print(str(cap.get(cv2.CAP_PROP_FPS)))

    translator = WorldToFrameTranslator((cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                                        table_size)
    tracker = Tracker()
    world = World(table_size)
    debug = Debug(translator)

    frame_throttler = FrameThrottler(desired_fps=10)

    with Robot("127.0.0.1", 9998) as robot:
        while (1):
            frame_throttler.throttle()

            _, frame = cap.read()
            frame = cv2.flip(frame, 1)

            puck_position = detect_puck_position(frame)
            if puck_position is None:
                continue

            puck_position = translator.f2w(puck_position)

            track = tracker.direction(*puck_position)
            if track is None:
                continue

            vector, velocity = track

            # puck_position = (900, 300)
            # vector = preprocessing.normalize(
            #     np.asarray([-1, -2.2]).reshape(1, -1)
            # )[0]
            # velocity = 100

            world.tick(PuckInfo(puck_position, vector, velocity))

            print(robot.get_position())
            print ('a')

            debug.draw(frame, world.get_debug(), fps=frame_throttler.fps)

            k = cv2.waitKey(5) & 0xFF
            if k == 27:
                break

    cv2.destroyAllWindows()
