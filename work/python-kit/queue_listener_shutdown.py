import logging
from logging.handlers import QueueHandler, QueueListener
from queue import SimpleQueue

class ReceiptCollector(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record.getMessage())

receipt_queue = SimpleQueue()
collector = ReceiptCollector()
queue_handler = QueueHandler(receipt_queue)
logger = logging.getLogger("aitrove.receipt.queue.contract")
logger.setLevel(logging.INFO)
logger.propagate = False
logger.addHandler(queue_handler)
listener = QueueListener(receipt_queue, collector)
listener.start()
try:
    logger.info("receipt %s accepted", "R-47")
    logger.info("receipt %s exported", "R-48")
finally:
    listener.stop()
    logger.removeHandler(queue_handler)
    queue_handler.close()
    collector.close()

print("delivered", collector.records)
