import logging
import time
from airhockey.controller import *
from airhockey.calibration import CalibrateHandler
from airhockey.vision.video import ScreenCapture, VideoStream
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
debug_window = DebugWindow(name="game",
                           translator=translator,
                           table_size=table_size,
                           color_ranges=[table_markers_color_range])

vision_query_context = QueryContext(translator=translator,
                                    frame_reader=video_stream,
                                    debug_window=debug_window)

calibrate_handler = CalibrateHandler(expected_markers=[PointF(400, 0), PointF(400, 600)],
                                     log="airhockey.calibrate",
                                     color_range=table_markers_color_range,
                                     vision_query_context=vision_query_context,
                                     tries=500,
                                     delay=1
                                     )

controller = Controller()
controller.register_handler(CalibrateControllerState,
                            calibrate_handler,
                            {
                                CalibrateHandler.SUCCESS: None,
                                CalibrateHandler.FAIL: IdleControllerState
                            })

video_stream.start()
while not video_stream.has_frame():
    time.sleep(0.1)

controller.start()
controller.run()
