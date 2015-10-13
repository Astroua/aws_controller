
import boto.s3
from boto.s3.connection import S3Connection
import os

try:
    from filechunkio import FileChunkIO
    NO_CHUNKIO_FLAG = False
except ImportError:
    NO_CHUNKIO_FLAG = True
    Warning("The filechunkio library could not be imported. Uploading large "
            "files will result in an error.")


def upload_to_s3(bucket_name, key_name, upload_item, key_metadata={},
                 create_bucket=False, chunksize=52428800, connection=None,
                 aws_access={}):
    '''
    Upload a file or folder to an S3 bucket. Optionally, a new bucket can be
    created. For files larger than 100 Mb, downloads are split into chunks.
    *This requires installing the FileChunkIO library.*

    Folder uploading is modeled from: https://gist.github.com/SavvyGuard/6115006

    '''

    # Create S3 connection if none are given.
    if connection is None:
        if "AWS_ACCESS_KEY_ID" in aws_access.keys() and "AWS_ACCESS_KEY_SECRET" in aws_access.keys():
            connection =S3Connection(**aws_access)
        elif len(aws_access.keys()) > 0:
            raise KeyError("aws_access must contain 'AWS_ACCESS_KEY_ID'"
                           " and 'AWS_ACCESS_KEY_SECRET'. All other"
                           " entries are ignored.")
        else:
            connection = s3.connection.S3Connection()
    else:
        if not isinstance(connection, S3Connection):
            raise TypeError("connection provided is not an S3 Connection.")

    # Check if that bucket exists. Otherwise create a new one if asked for.





def download_from_s3(bucket_name):
    pass


def remove_s3_bucket(bucket_name):
    pass

