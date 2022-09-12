import logging

from airhockey.controller import Controller
from airhockey.handlers.await_video import AwaitVideoHandler
from airhockey.handlers.check_network import CheckNetworkHandler
from airhockey.handlers.detect_players import DetectPlayersHandler
from airhockey.handlers.detect_table import DetectTableHandler
from airhockey.handlers.failed import FailedHandler
from airhockey.handlers.play_game import PlayGameHandler
from airhockey.handlers.test_moves import TestMovesHandler
from airhockey.robot import Robot
from airhockey.vision.video import ScreenCapture
from airhockey.vision.color import ColorRange
from airhockey.vision.query import QueryContext
from airhockey.translate import WorldToFrameTranslator
from airhockey.debug import DebugWindow

logger = logging.getLogger("airhockey")
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)
logger.info("Welcome")

robot_host = 'localhost'
robot_port = 1133

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
                              h_low=49,
                              h_high=69,
                              sv_low=53)

robot_pusher_color_range = ColorRange(name="Robot Pusher",
                                      h_low=20,
                                      h_high=30,
                                      sv_low=53)

debug_window = DebugWindow(name="game",
                           log="airhockey",
                           translator=translator,
                           table_size=table_size,
                           color_ranges=[table_markers_color_range,
                                         puck_color_range,
                                         robot_pusher_color_range])

vision_query_context = QueryContext(translator=translator,
                                    frame_reader=video_stream,
                                    debug_window=debug_window)

await_video_handler = AwaitVideoHandler(video_stream=video_stream, timeout=10)

detect_table_handler = DetectTableHandler(
    expected_markers=[(400, 0), (400, 600)],
    color_range=table_markers_color_range,
    vision_query_context=vision_query_context,
    tries=500,
    delay=1,
    success_retries=10
    )

detect_players_handler = DetectPlayersHandler(
    vision_query_context=vision_query_context,
    puck_color_range=puck_color_range,
    robot_pusher_color_range=robot_pusher_color_range,
    tries=500,
    delay=1)

check_network_handler = CheckNetworkHandler(
    host=robot_host,
    port=robot_port,
    tries=500,
    delay=5
)

test_moves_handler = TestMovesHandler(
    destinations=[
        (300, 300),
        (50, 50),
        (550, 50),
        (550, 550),
        (50, 550),
        (50, 50),
        (300, 300),
    ],
    robot=Robot(host=robot_host, port=robot_port),
    vision_query_context=vision_query_context,
    robot_pusher_color_range=robot_pusher_color_range,
    delay=3
)

play_game_handler = PlayGameHandler(
    vision_query_context=vision_query_context,
    puck_color_range=puck_color_range,
    pusher_color_range=robot_pusher_color_range
)

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
        await_video_handler.SUCCESS: PLAY_GAME,
        await_video_handler.TIMEOUT: FAILED_STATE,
    }),
    DETECT_TABLE: (detect_table_handler, {
        detect_table_handler.SUCCESS: DETECT_PLAYERS,
        detect_table_handler.FAIL: FAILED_STATE,
    }),
    DETECT_PLAYERS: (detect_players_handler, {
        detect_players_handler.SUCCESS: CHECK_NETWORK,
        detect_players_handler.FAIL: FAILED_STATE,
    }),
    CHECK_NETWORK: (check_network_handler, {
        check_network_handler.SUCCESS: TEST_MOVES,
        check_network_handler.FAIL: FAILED_STATE
    }),
    TEST_MOVES: (test_moves_handler, {
        test_moves_handler.SUCCESS: PLAY_GAME,
        test_moves_handler.FAIL: FAILED_STATE
    }),
    PLAY_GAME: (play_game_handler, {
        play_game_handler.SUCCESS: FAILED_STATE,
        play_game_handler.FAIL: FAILED_STATE
    })
}

controller = Controller(AWAIT_VIDEO, FAILED_STATE)
for state in state_transitions:
    handler, result_map = state_transitions[state]
    controller.register_handler(state, handler, result_map)

controller.run()
