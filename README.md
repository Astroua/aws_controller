# aws_controller

Basic scripts to automate EC2 instances on AWS. We're radio astronomers, so built-in is the ability to install CASA, along with some add-ons.

**The instructions assume you have your aws credentials configured.**
**Run 'aws configure' to do so.**

Requires
--------
* boto
* paramiko
* awscli
* FileChunkIO (optional for uploading large files)

Launching an instance
---------------------
An instance can be launched using the ```launch``` function:
```
# Assuming you are in the aws_controller directory
from launch_instance import launch
instance = launch("mykey", image_id='ami-00000000',
                  instance_type='t2.small',
                  security_groups='default')
```
Once it is running, the function returns an instance object, from which you can control it. Or, ssh into it as normal using the same key name provided to launch the instance. **The key must be registered in AWS to work.**

Creating an image
-----------------
An image can be created running ```create_root_drive.py``` by importing into a python session:
```
# Assuming you are in the aws_controller directory
from create_root_drive import create_root_drive
create_root_drive("new_image", "/path/to/key.pem",
                  install_kwargs={"install_casa": True})
```
Or by running from the command line:
```
python create_root_drive.py True False "/path/to/key.pem"
```
These two calls are equivalent, and will install CASA 4.3 on a new image. By default, the original image is ubuntu 14.04 (ami code from us-west-2 or Oregon region).
*Note: A timestamp is attached to the image name provided.*

When completed, you should see a new image registered on the AWS EC2 console.

Uploading to S3
---------------------------
S3 buckets can be created and accessed using the functions in `upload_download_s3.py`.
Files and folders can be uploaded by running:
```
from upload_download_s3 import upload_to_s3
upload_to_s3("mybucket", "myfile")
```
The function will automatically invoke a multi-part upload for large file (set by `chunksize` with a default of 50 Mb). This requires the FileChunkIO package (installable via pip: `pip install FileChunkIO`). *If your AWS credentials are not set, you must specify them with the aws_access keyword as a dictionary.*

The above call assumes that "mybucket" pre-exists on S3. To create a new bucket:
```
upload_to_s3("mybucket", "myfile", create_bucket=True)
```
An error is returned if that bucket name already exists.
`upload_to_s3` automatically recognizes a folder input, and will upload each file in the folder, reproducing the internal file structure.

Keys can be deleted from a bucket with:
```
remove_s3_key('mykey', 'mybucket', s3_connection)
```

The `s3_connection` is a boto class (see [the tutorial](http://boto.readthedocs.org/en/latest/s3_tut.html#creating-a-connection)).

Entire buckets can also be deleted:
```
remove_s3_bucket('mybucket', s3_connection)
```

Downloading from S3
-------------------
To download a file from an S3 bucket:
```
from upload_download_s3 import download_from_s3
download_from_s3('mykey', 'my_bucket')
```
You should now see the file name `mykey` will be downloaded. If the file is in folder structure in the bucket, the filename itself will be the downloaded filename ("path/to/myfile.txt" becomes "myfile.txt").
Wildcards can be used to download groups of keys from a bucket:
```
download_from_s3('mykeys/*', 'my_bucket')
```
will download all keys in the bucket beginning with `mykeys/*`. The output directory can be specified with the `output_dir` argument.


Developers
----------
* Eric Koch [@e-koch](https://github.com/e-koch)
* Alex Tetarenko [@tetarenk](https://github.com/tetarenk)
* Greg Sivakoff [@radioastronomer](https://github.com/radioastronomer)
* Erik Rosolowsky [@low-sky](https://github.com/low-sky)

Support from the SKA AstroCompute Program.
