import logging
import time
from airhockey.controller import *
from airhockey.handlers.detect_players import DetectPlayersHandler
from airhockey.handlers.detect_table import DetectTableHandler
from airhockey.handlers.failed import FailedHandler
from airhockey.vision.video import ScreenCapture
from airhockey.vision.color import ColorRange
from airhockey.vision.query import QueryContext
from airhockey.translate import WorldToFrameTranslator
from airhockey.debug import DebugWindow
from airhockey.geometry import PointF

logger = logging.getLogger("airhockey")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)
logger.info("Welcome")

table_size = (1200, 600)
frame_size = (1280, 768)
video_stream = ScreenCapture(frame_size)
# video_stream = VideoStream(0, frame_size)
translator = WorldToFrameTranslator(frame_size, table_size)

table_markers_color_range = ColorRange(name="Table Markers",
                                       h_low=84,
                                       h_high=92,
                                       sv_low=53)

puck_color_range = ColorRange(name="Puck",
                              h_low=84,
                              h_high=92,
                              sv_low=53)

robot_pusher_color_range = ColorRange(name="Robot Pusher",
                                      h_low=84,
                                      h_high=92,
                                      sv_low=53)


debug_window = DebugWindow(name="game",
                           translator=translator,
                           table_size=table_size,
                           color_ranges=[table_markers_color_range])

vision_query_context = QueryContext(translator=translator,
                                    frame_reader=video_stream,
                                    debug_window=debug_window)

detect_table_handler = DetectTableHandler(expected_markers=[PointF(400, 0), PointF(400, 600)],
                                          color_range=table_markers_color_range,
                                          vision_query_context=vision_query_context,
                                          tries=500,
                                          delay=1
                                          )

detect_players_handler = DetectPlayersHandler(vision_query_context=vision_query_context,
                                              puck_color_range=puck_color_range,
                                              robot_pusher_color_range=robot_pusher_color_range,
                                              tries=500)

failed_handler = FailedHandler()


FAILED_STATE = "FAILED_STATE"
DETECT_TABLE = "DETECT_TABLE"
DETECT_PLAYERS = "DETECT_PLAYERS"
CHECK_NETWORK = "CHECK_NETWORK"
TEST_MOVES = "TEST_MOVES"
PLAY_GAME = "PLAY_GAME"

controller = Controller(DETECT_TABLE, FAILED_STATE)
controller.register_handler(FAILED_STATE, failed_handler, {})
controller.register_handler(DETECT_TABLE,
                            detect_table_handler,
                            {
                                detect_table_handler.SUCCESS: DETECT_PLAYERS,
                                detect_table_handler.FAIL: FAILED_STATE
                            })
controller.register_handler(DETECT_PLAYERS,
                            detect_players_handler,
                            {
                                detect_players_handler.SUCCESS: CHECK_NETWORK,
                                detect_players_handler.FAIL: FAILED_STATE
                            })

video_stream.start()
while not video_stream.has_frame():
    time.sleep(0.1)

controller.run()
