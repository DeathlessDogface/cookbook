from sys import stdout
from time import sleep

__all__ = ['progress_bar']


class ColorHandler(object):
    GREEN = "\033[01;32m"
    BLUE = "\033[01;34m"
    NO = "\033[00m"
    STRESS = "\033[7m"


def progress_bar(current, total, msg=None, length=100):
    progress = (current * 1.0) / total
    if not msg:
        msg = "{:.2f}%".format(progress * 100)
    bar = str(msg).center(length, "_")
    length = len(bar)
    pro_index = int(length * progress)
    line = "\r{}{}{}{}".format(ColorHandler.STRESS, bar[:pro_index], ColorHandler.NO, bar[pro_index:])
    stdout.write(line)
    stdout.flush()


if __name__ == "__main__":
    for i in xrange(70):
        sleep(1)
        progress_bar(i+1, 70,length=50)
