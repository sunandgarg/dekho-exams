import io
import logging

captured = io.StringIO()
logger = logging.getLogger("aitrove.receipts.fixture")
logger.handlers.clear()
logger.propagate = False
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(captured)
handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
logger.addHandler(handler)
try:
    logger.info("receipt=%s outcome=%s", 41, "accepted")
    print(captured.getvalue().strip())
finally:
    logger.removeHandler(handler)
    handler.close()
