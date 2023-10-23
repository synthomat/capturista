import logging
import threading


class Consumer(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._stop_event = threading.Event()

    def run(self):
        logging.info("Task Consumer started")
        """
        while not self._stop_event.is_set():
            task = TASK_QUEUE.get()
            capture_type = task.capture_type
            # LOADERS[_id]["status"] = "started"
            loader_cls = LOADER_TYPES.get(capture_type, None)

            if not loader_cls:
                continue

            try:
                loader = loader_cls(manager, task)
                loader.run()
            except Exception as e:
                logging.error(e)
        """
        logging.info("Task Consumer stopped")

class Scheduler(threading.Thread):
    """"""

    def __init__(self):
        super().__init__(daemon=True)

    def run(self):
        """
        logging.info("Task Scheduler started")
        capture_configs = db.table('capture_configs')

        while True:
            sources = capture_configs.search(Query().autoload == True)

            for config in sources:
                task = CaptureTask(
                    config['id'],
                    config['capture_type'],
                    params=config.get('params'),
                    slot_params=config.get('slot_params')
                )

                TASK_QUEUE.put(task)

            time.sleep(60 * 30)

        logging.info("Task Scheduler stopped")
        """