import logging
import time
from airhockey.controller import *
from airhockey.handlers.await_video import AwaitVideoHandler
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
                              h_low=30,
                              h_high=40,
                              sv_low=53)

robot_pusher_color_range = ColorRange(name="Robot Pusher",
                                      h_low=20,
                                      h_high=30,
                                      sv_low=53)


debug_window = DebugWindow(name="game",
                           log="airhockey",
                           translator=translator,
                           table_size=table_size,
                           color_ranges=[table_markers_color_range, puck_color_range, robot_pusher_color_range])

vision_query_context = QueryContext(translator=translator,
                                    frame_reader=video_stream,
                                    debug_window=debug_window)

await_video_handler = AwaitVideoHandler(video_stream=video_stream, timeout=10)

detect_table_handler = DetectTableHandler(expected_markers=[PointF(400, 0), PointF(400, 600)],
                                          color_range=table_markers_color_range,
                                          vision_query_context=vision_query_context,
                                          tries=500,
                                          delay=1
                                          )

detect_players_handler = DetectPlayersHandler(vision_query_context=vision_query_context,
                                              puck_color_range=puck_color_range,
                                              robot_pusher_color_range=robot_pusher_color_range,
                                              tries=500,
                                              delay=1)

failed_handler = FailedHandler()


FAILED_STATE = "FAILED_STATE"
AWAIT_VIDEO = "AWAIT_VIDEO"
DETECT_TABLE = "DETECT_TABLE"
DETECT_PLAYERS = "DETECT_PLAYERS"
CHECK_NETWORK = "CHECK_NETWORK"
TEST_MOVES = "TEST_MOVES"
PLAY_GAME = "PLAY_GAME"

state_transitions = {
    FAILED_STATE: (failed_handler, {}),
    AWAIT_VIDEO: (await_video_handler, {
        await_video_handler.SUCCESS: DETECT_TABLE,
        await_video_handler.TIMEOUT: FAILED_STATE,
    }),
    DETECT_TABLE: (detect_table_handler, {
        detect_table_handler.SUCCESS: DETECT_PLAYERS,
        detect_table_handler.FAIL: FAILED_STATE,
    }),
    DETECT_PLAYERS: (detect_players_handler, {
        detect_players_handler.SUCCESS: CHECK_NETWORK,
        detect_players_handler.FAIL: FAILED_STATE,
    })
}

controller = Controller(AWAIT_VIDEO, FAILED_STATE)
for state in state_transitions:
    handler, result_map = state_transitions[state]
    controller.register_handler(state, handler, result_map)

controller.run()
