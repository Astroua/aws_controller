
from controller import WORKER_SCRIPT
from launch_instance import launch
from upload_download_s3 import upload_to_s3, download_from_s3, remove_s3_bucket
from utils import timestring

from boto import sqs, ec2, s3
from boto import Config
import json
from time import sleep
import os

# Assuming that the testing system has the AWS config already set.
try:
    proc_name = "aws_ska_test_worker_" + timestring()
    region = "us-west-2"

    # Read in credentials
    config = Config()
    config.load_credential_file(os.path.join(os.path.expanduser("~"),".aws/credentials"))
    info = config.items("default")[2:]
    key = info[0][1]
    secret = info[1][1]

    # Create a test file and upload to S3
    if not os.path.exists("tests/test.txt"):
        test_string = "ALLGLORYTOTHEHYPNOTOAD"

        with open("tests/test.txt", "w") as f:
            f.write(test_string)

    print("Uploading to S3")

    upload_to_s3(proc_name, "tests/test.txt", key_prefix="data/",
                 aws_access={"aws_access_key_id": key,
                             "aws_secret_access_key": secret},
                 create_bucket=True)

    # Create an SQS queue and message for the worker
    queue = sqs.connect_to_region(region).create_queue(proc_name)

    mess = {}
    mess["proc_name"] = proc_name
    mess["bucket"] = proc_name
    mess['key_name'] = "data/test.txt"
    mess['command'] = ["ls", "/home/ubuntu/data/"]
    mess['parameters'] = ""

    mess = queue.new_message(body=json.dumps(mess))
    queue.write(mess)

    print("Launching instance")

    # Launch an instance with the worker script
    user_data = WORKER_SCRIPT \
        % {"USER": "ubuntu",
           "QUEUE_NAME": proc_name,
           "REGION": region,
           "KEY": key,
           "SECRET": secret,
           "RESP_QUEUE_NAME": proc_name + "_response"}

    inst = launch(key_name=None, region=region, image_id="ami-22decf43",
                  user_data=user_data)

    # sleep 5 min
    sleep(120)

    if inst.state == u"running":
        print("Terminating after 5 min.")
        inst.terminate()

    print("Checking for response message.")

    resp_queue = sqs.connect_to_region(region).create_queue(proc_name + "_response")

    if resp_queue.count() > 0:
        mess = resp_queue.read(10)
        content = json.loads(mess.get_body())
        print("Saving content.")
        with open("tests/test_response.txt", "w") as f:
            json.dump(content, f)
    else:
        print("No message received!")
except Exception as e:
    print("Failed with :")
    print(e)

queue.delete()
resp_queue.delete()
remove_s3_bucket(proc_name, s3.connection.S3Connection())