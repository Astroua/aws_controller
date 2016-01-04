# License under the MIT License - see LICENSE

from datetime import datetime
import os


def timestring():
    TimeString = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return TimeString


def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]
