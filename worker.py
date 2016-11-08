# License under the MIT License - see LICENSE

import boto
from boto import sqs
import json
from subprocess import Popen, PIPE
import os
import traceback as tr

from upload_download_s3 import download_from_s3, upload_to_s3
from utils import listdir_fullpath


class Worker(object):
    """docstring for Worker"""
    def __init__(self, queue_name, key, secret, region='us-west-2'):

        self.queue_name = queue_name
        self.message_dict = {}

        self.credentials = {'aws_access_key_id': key,
                            'aws_secret_access_key': secret}
        self.key = key
        self.secret = secret
        self.region = region

        self.success = True
        self.empty_flag = False

    def receive_message(self, max_time=3600, save_message=True):
        '''
        Connect to the queue and read the next message.
        '''

        queue = sqs.connect_to_region(self.region,
                                           aws_access_key_id=self.key,
                                           aws_secret_access_key=self.secret).create_queue(self.queue_name)
        # Get the message from the queue within some max time
        mess = queue.read(max_time)

        if mess is None:
            self.empty_flag = True
            self.success = False
            self.message_dict['receive_message'] = "Found no message to read."
        else:
            contents = json.loads(mess.get_body())

            self.proc_name = contents['proc_name']
            self.bucket_name = contents['bucket']
            self.key_name = contents['key_name']
            self.command = contents['command']

            try:
                queue.delete_message(mess)
            except Exception:
                print("No message to delete.")

            if save_message:
                with open("data/params.txt", "w") as f:
                    json.dump(contents, f)

            self.message_dict['receive_message'] = "Successfully read message."

    def download_data(self):
        if not self.empty_flag:
            try:
                download_from_s3(self.key_name, self.bucket_name,
                                 aws_access=self.credentials)
                self.message_dict['download_data'] = \
                    "Successfully downloaded data."
            except Exception:
                self.success = False
                self.message_dict['download_data'] = tr.format_exc()

    def execute(self):
        if not self.empty_flag:
            try:
                stdout_file = open("data_products/stdout.txt", "a")
                stderr_file = open("data_products/stderr.txt", "a")
                for cmd in self.command:
                    if not isinstance(cmd, list):
                        cmd = cmd.split()
                    proc = Popen(cmd, stdout=stdout_file, stderr=stderr_file)
                    proc.communicate()
                    stdout_file.flush()
                stdout_file.close()
                # Put a copy of the parameter file for the job into the
                # data_products folder.
                os.system("cp /home/ubuntu/data/params.txt "
                          "/home/ubuntu/data_products/")
                # Check the files in the output folder
                self.output_files = listdir_fullpath("/home/ubuntu/data_products/")
                if len(self.output_files) == 0:
                    raise Exception("No output files found.")
                self.message_dict['execute'] = "Successfully executed command."

            except Exception:
                self.success = False
                self.message_dict['execute'] = tr.format_exc()
                self.output_files = []
                try:
                    stdout_file.close()
                except Exception:
                    pass

    def upload_results(self, make_tar=False):

        if not self.empty_flag:
            if len(self.output_files) == 0:
                self.message_dict['upload_results'] = "No output files found."
            else:
                if make_tar:
                    # Create a tar file and only upload it.
                    import tarfile
                    tar = tarfile.open("data_products.tar", "w:")
                    for name in self.output_files:
                        tar.add(name)
                    tar.close()
                    self.output_files = ["data_products.tar"]

                try:
                    for out in self.output_files:
                        upload_to_s3(self.bucket_name, out,
                                     aws_access=self.credentials,
                                     create_bucket=False,
                                     key_prefix="data_products/")
                    self.message_dict['upload_results'] = \
                        "Successfully uploaded results."
                except Exception:
                    self.message_dict['upload_results'] = tr.format_exc()
                    self.success = False

    def send_result_message(self, resp_queue_name):
        resp_queue = sqs.connect_to_region(self.region,
                                           aws_access_key_id=self.key,
                                           aws_secret_access_key=self.secret).create_queue(resp_queue_name)
        resp_message = {'proc_name': self.proc_name,
                        'success': self.success,
                        'messages': self.message_dict}

        mess = resp_queue.new_message(body=json.dumps(resp_message))
        resp_queue.write(mess)
