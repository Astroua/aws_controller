# License under the MIT License - see LICENSE

from datetime import datetime


def timestring():
    TimeString = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return TimeString