
'''
Control the whole thing.
'''

import boto
import json


WORKER_SCRIPT="""#!/bin/bash

HOME=/home/USER

cd $HOME

$HOME/miniconda/bin/python -c "from aws_controller import Worker

work = Worker.from_queue(queue_name)

work.download_data()

work.execute()

work.upload_results()

work.send_result_message()
"

/sbin/shutdown now -h
"""


class Controller(object):
    """docstring for Controller"""
    def __init__(self, arg):
        super(Controller, self).__init__()
        self.arg = arg

    def upload_request(self):
        pass

    def new_sqs_message(self, queue=None):
        pass

    def num_in_queue(self, queue):
        pass

    def boot_instances(self, **kwargs):
        pass

    def check_workers(self, queue):
        pass

    def receive_result(self, queue):
        pass

    def check_finish(self):
        pass

    def mass_shutdown(self):
        pass
