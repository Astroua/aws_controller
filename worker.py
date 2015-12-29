
import boto
import boto.sqs as sqs
import boto.s3 as s3
import json
from subprocess import Popen, PIPE
import os

from upload_download_s3 import download_from_s3, upload_to_s3


class Worker(object):
    """docstring for Worker"""
    def __init__(self, queue, key, secret):
        super(Worker, self).__init__()
        self.queue = boto.connect_sqs(key, secret).create_queue(queue)
        self.message_dict = None

        self.credentials = {'key': key, 'secret': secret}

        self.success = True
        self.empty_flag = False

    @staticmethod
    def from_queue(queue):

        self = Worker(queue)
        self.receive_message()

        return self

    def receive_message(self, max_time=3600):
        '''
        Connect to the queue and read the next message.
        '''

        # Get the message from the queue within some max time
        mess = self.queue.read(max_time)

        if mess is None:
            self.empty_flag = True
            self.success = False
            self.message_dict['receive_message'] = "Found no message to read."
        else:
            contents = json.loads(mess.get_body())

            self.proc_name = contents['proc_name']
            self.bucket_name = contents['bucket']
            self.key_name = contents['key_name']
            self.output_queue = contents['out_queue']
            self.command = contents['command']
            self.parameters = contents['parameters']

            self.queue.delete_message(mess)

            self.message_dict['receive_message'] = "Successfully read message."

    def download_data(self, bucket):
        if not self.empty_flag:
            try:
                download_from_s3(self.key_name, self.bucket_name,
                                 aws_access=self.credentials,
                                 output_dir="data/")
                self.message_dict['download_data'] = "Successfully downloaded data."
            except Exception as e:
                self.success = False
                self.message_dict['download_data'] = e

    def execute(self):
        if not self.empty_flag:
            try:
                proc = Popen(self.command, stderr=PIPE, stdout=PIPE)
                # Check the files in the output folder
                self.output_files = os.listdir("data_output")
                if len(self.output_files) == 0:
                    raise Exception("No output files found.")
                self.message_dict['execute'] = "Successfully executed command."

            except Exception as e:
                self.success = False
                self.message_dict['execute'] = e

    def upload_results(self):

        if not self.empty_flag:
            if len(self.output_files) == 0:
                self.message_dict['upload_results'] = "No output files found."
            else:
                try:
                    for out in self.output_files:
                        upload_to_s3(self.bucket_name, out,
                                     aws_access=self.credentials,
                                     create_bucket=False)
                    self.message_dict['upload_results'] = "Successfully uploaded results."
                except Exception as e:
                    self.message_dict['upload_results'] = e
                    self.success = False

    def send_result_message(self, queue_name):
        resp_queue = boto.connect_sqs(self.key, self.secret).create_queue(queue_name)
        resp_message = {'proc_name': self.proc_name,
                        'success': self.success,
                        'messages': self.message_dict}

        resp_queue.new_message(body=json.dumps(resp_message))
