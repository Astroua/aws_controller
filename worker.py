
import boto.sqs as sqs
import boto.s3 as s3
import json

from upload_download_s3 import download_from_s3, upload_to_s3


class Worker(object):
    """docstring for Worker"""
    def __init__(self, queue):
        super(Worker, self).__init__()
        self.queue = queue
        self.message_dict = None

    @staticmethod
    def from_queue(queue):

        self = Worker(queue)
        self.receive_message()

        return self

    def receive_message(self):
        '''
        Connect to the queue and read the next message.
        '''

        mess = self.queue.read()

        if mess is None:
            self.empty_flag = True
        else:
            contents = json.loads(mess.get_body())

            self.empty_flag = False
            self.bucket_name = contents['bucket']
            self.key_name = contents['key_name']
            self.out_bucket_name = contents['out_bucket']
            self.output_queue = contents['out_queue']
            self.credentials = contents['credentials']

            self.queue.delete_message(mess)

    def download_data(self, bucket):
        if self.empty_flag:
            pass
        else:
            download_from_s3(self.key_name, self.bucket_name,
                             aws_access=self.credentials)

    def execute(self):
        if self.empty_flag:
            pass
        else:
            # DO SOMETHING
            self.output_files = []

    def send_result_message(self):
        if self.empty_flag:
            pass

    def upload_results(self):
        if self.empty_flag:
            pass
        else:
            if len(self.output_files) == 0:
                self.logger(self.upload_results.im_func.func_name,
                            "No output files created.")
                return
            for out in self.output_files:
                upload_to_s3(self.out_bucket_name, out,
                             aws_access=self.credentials,
                             create_bucket=True)

    def logger(self, function, message):
        pass
