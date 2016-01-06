# License under the MIT License - see LICENSE

from datetime import datetime
import os
import time


def timestring():
    TimeString = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return TimeString


def human_time():
    now = datetime.fromtimestamp(time.time())
    return now.strftime('%Y-%m-%d %H:%M:%S')


def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]
