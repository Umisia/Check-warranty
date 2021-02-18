import logging
import config

class Logger:
    def __init__(self, name):

        formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")
        stream_formatter = logging.Formatter("%(name)s: %(message)s")

        file_handler = logging.FileHandler(config.logs_path)
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(stream_formatter)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(stream_handler)

