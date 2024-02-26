import logging
from logging.handlers import RotatingFileHandler
import os

class Logger(object):

    def __init__(self, app_name='logger', maxBytes=10*1024*1024, backupCount=10):
        self.app_name = app_name
        self.log_folder = f"/var/log/{app_name}"
        self.log_path = os.path.join(self.log_folder, f"{self.app_name.lower()}.log")
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(logging.DEBUG)

        if not os.path.exists(os.path.dirname(self.log_path)):
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        # Create a handler, used for output to a file
        file_handler = RotatingFileHandler(self.log_path, maxBytes=maxBytes, backupCount=backupCount)
        file_handler.setLevel(logging.DEBUG)

        # Create a handler, used for output to the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Define the output format of handler
        formatter = logging.Formatter('%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s', datefmt='%y/%m/%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add the handler to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def __call__(self, msg: str = None, level='DEBUG'):
        if level == 'DEBUG':
            self.logger.debug(msg)
        elif level == 'INFO':
            self.logger.info(msg)
        elif level == 'WARNING':
            self.logger.warning(msg)
        elif level == 'ERROR':
            self.logger.error(msg)
        elif level == 'CRITICAL':
            self.logger.critical(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def critical(self, msg: str):
        self.logger.critical(msg)

    def info(self, msg: str):
        self.logger.info(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)
