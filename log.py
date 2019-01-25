import logging
import logging.handlers
import os.path


class Logger(logging.getLoggerClass()):
    def __init__(self, name, console=True, file_path=None, debug=False):
        self.handlers = []
        self.disabled = False
        self.name = name
        self.filters = []
        self.propagate = False
        if debug:
            self.level = logging.DEBUG
        else:
            self.level = logging.INFO
        self._set_file(file_path)
        self._set_handler(console)

    @property
    def rtHandler(self):
        Rthandler = logging.handlers.RotatingFileHandler(
            self.file_path, maxBytes=10 * 1024 * 1024, backupCount=5)
        Rthandler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt="\n".join([
                "%(asctime)s.%(msecs)03d",
                "%(process)d %(processName)s   %(thread)d  %(threadName)s",
                "%(pathname)s %(filename)s+%(lineno)s %(name)s %(funcName)s %(module)s",
                "%(created)f %(relativeCreated)d",
                "%(levelname)-8s %(levelno)s",
                "%(context)s %(message)s"
            ]),
            datefmt='%y-%m-%d %H:%M:%S')
        Rthandler.setFormatter(formatter)
        return Rthandler

    @property
    def consoleHandler(self):
        console = ColorHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt='%(asctime)s|%(name)s|%(process)d|%(colorBegin)s%(levelname)-8s%(colorEnd)s|%(message)s',
            datefmt='%H:%M:%S')
        console.setFormatter(formatter)
        return console

    def _set_handler(self, console):
        self.addHandler(self.rtHandler)
        if console:
            self.addHandler(self.consoleHandler)

    def _set_file(self, file_path):
        file_name = "{}.log".format(self.name)
        dir_path = os.path.abspath(os.path.curdir)
        if file_path:
            if os.path.isfile(file_path):
                self.file_path = file_path
                return
            if os.path.isdir(file_path):
                dir_path = os.path.abspath(file_path)
            else:
                if os.path.sep in file_path:
                    p, n = os.path.split(file_path)
                else:
                    p, n = dir_path, file_path
                dir_path = os.path.abspath(p)
                if n.endswith('.log'):
                    file_name = n
                else:
                    file_name = "{}.log".format(n)
        self.file_path = os.path.join(dir_path, file_name)


class ColorHandler(logging.StreamHandler):
    LEVEL_COLORS = {
        logging.DEBUG: '\033[00;32m',  # GREEN
        logging.INFO: '\033[00;36m',  # CYAN
        # logging.AUDIT: '\033[01;36m',  # BOLD CYAN
        logging.WARN: '\033[01;33m',  # BOLD YELLOW
        logging.ERROR: '\033[01;31m',  # BOLD RED
        logging.CRITICAL: '\033[01;31m',  # BOLD RED
    }

    def format(self, record):
        record.colorBegin = self.LEVEL_COLORS[record.levelno]
        record.colorEnd = "\033[0m"
        return logging.StreamHandler.format(self, record)


cache = {}


def getLogger(name='default', console=True, file_path=None, debug=False):
    if name not in cache:
        cache[name] = Logger(name=name, console=console, file_path=file_path, debug=debug)
    return cache[name]


def test():
    LOG = getLogger(name='test', file_path='testLog', debug=True)
    LOG.debug("this is a debug")
    LOG.info("this is a info")
    LOG.warn("this is a warn")
    LOG.error("this is a error")
    LOG.critical("this is a critical")


if __name__ == '__main__':
    test()
