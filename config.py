import logging

log_level = logging.INFO
logging.basicConfig(filename="mgr.log", format='%(levelname)s - %(lineno)s - %(message)s', level=log_level)
loggers = {}


def get_logger(name):
    if name not in loggers:
        loggers[name] = logging.getLogger(name)
    return loggers[name]


http_port = 8888