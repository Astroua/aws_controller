
'''
Control the whole thing.
'''

import boto
import json

from utils import timestring
from upload_download_s3 import download_from_s3, upload_to_s3


WORKER_SCRIPT = """#!/bin/bash

export HOME=/home/%(USER)s

cd $HOME

cd aws_controller
/usr/bin/git pull
cd ..

%(CUSTOM_LINES)s

$HOME/miniconda2/bin/python -c "from aws_controller.worker import Worker

work = Worker('%(QUEUE_NAME)s', '%(KEY)s', '%(SECRET)s', '%(REGION)s')

work.receive_message()

work.download_data()

work.execute()

work.upload_results(make_tar=True)

work.send_result_message('%(RESP_QUEUE_NAME)s')
"

/sbin/shutdown now -h
"""


class Controller(object):
    """docstring for Controller"""
    def __init__(self, params, run_name='CASA_Timing', region='us-west-2',
                 key=None, secret=None, max_instances=10):
        super(Controller, self).__init__()
        self.params = params

        self.njobs = params['njobs']
        self.data_files = params['files']
        self.max_instances = max_instances

        self.key = key
        self.secret = secret
        self.credentials = {"aws_access_key_id": self.key,
                            "aws_secret_access_key": self.secret}

        self.job_name = run_name + "_" + timestring()

        self.request_queue_name = self.job_name + "_request"
        self.request_queue = \
            boto.sqs.connect_to_region(region,
                                       aws_access_key_id=self.key,
                                       aws_secret_access_key=self.secret).create_queue(self.request_queue_name)

        self.result_queue_name = self.job_name + "_result"
        self.result_queue = \
            boto.sqs.connect_to_region(region,
                                       aws_access_key_id=self.key,
                                       aws_secret_access_key=self.secret).create_queue(self.result_queue_name)


    def upload_request(self, data, bucket_name=None):
        '''
        Upload any given data to S3.
        '''

        if bucket_name is not None:
            create_bucket = False
        else:
            bucket_name = self.job_name
            create_bucket = True

        if not isinstance(data, list):
            data = [data]

        self._track_uploaded = dict.fromkeys(data)

        for dat in data:
            try:
                upload_to_s3(bucket_name, dat, create_bucket=create_bucket,
                             aws_access=self.credentials)
                self._track_uploaded[dat] = "Success"
            except Exception as e:
                self._track_uploaded[dat] = "Failed with: " + e
                return False

        return True

    @property
    def track_uploaded(self):
        return self._track_uploaded


    def new_sqs_message(self):
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
