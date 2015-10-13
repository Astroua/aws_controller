# License under the MIT License - see LICENSE

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import os
import math

from utils import timestring

try:
    from filechunkio import FileChunkIO
    NO_CHUNKIO_FLAG = False
except ImportError:
    NO_CHUNKIO_FLAG = True
    Warning("The filechunkio library could not be imported. Uploading large "
            "files will result in an error.")


def upload_to_s3(bucket_name, upload_item, key_metadata={},
                 create_bucket=False, chunksize=52428800, conn=None,
                 aws_access={}):
    '''
    Upload a file or folder to an S3 bucket. Optionally, a new bucket can be
    created. For files larger than 100 Mb, downloads are split into chunks.
    *This requires installing the FileChunkIO library.*

    Folder uploading is modeled from: https://gist.github.com/SavvyGuard/6115006

    '''

    # Create S3 connection if none are given.
    if conn is None:
        if "AWS_ACCESS_KEY_ID" in aws_access.keys() and "AWS_ACCESS_KEY_SECRET" in aws_access.keys():
            conn = S3Connection(**aws_access)
        elif len(aws_access.keys()) > 0:
            raise KeyError("aws_access must contain 'AWS_ACCESS_KEY_ID'"
                           " and 'AWS_ACCESS_KEY_SECRET'. All other"
                           " entries are ignored.")
        else:
            # Use the AWS Keys saved on your machine.
            conn = s3.connection.S3Connection()
    else:
        if not isinstance(conn, S3Connection):
            raise TypeError("conn provided is not an S3 Connection.")

    # Check if that bucket exists. Otherwise create a new one if asked for.
    bucket_exists = True if bucket_name in conn.get_all_buckets() else False

    if bucket_exists and create_bucket:
        raise Warning("The bucket name given '" + bucket_name +
                      "' already exists.")

    if create_bucket:
        bucket = conn.create_bucket(bucket_name)
    else:
        bucket = conn.get_bucket(bucket_name)

    # Check if the given key (ie. file or folder name) already exists in
    # the bucket.

    key_name = upload_item.split("/")[-1]

    # Now check if the item to upload is a file or folder
    if os.path.isdir(upload_item):
        pass
    elif os.path.isfile(upload_item):
        auto_multipart_upload(upload_item, bucket, key_name)
    else:
        raise TypeError(upload_item + " is not an existing file or folder."
                        " Check given input.")


def auto_multipart_upload(filename, bucket, key_name, max_size=104857600,
                          chunk_size=52428800):
    '''
    Based on the size of the file to be uploaded, automatically partition into
    a multi-part upload.
    '''

    source_size = os.stat(filename).st_size

    if key_name in bucket.get_all_keys():
        raise KeyError(key_name + " already exists in the bucket " +
                       bucket.name + ". Please choose a new key name.")

    if source_size > max_size:
        mp = bucket.initiate_multipart_upload(key_name)

        nchunks = int(math.ceil(source_size / float(chunk_size)))

        for i in range(nchunks):
            offset = chunk_size * i
            bytes = min(chunk_size, source_size - offset)
            with FileChunkIO(filename, 'r', offset=offset, bytes=bytes) as fp:
                mp.upload_part_from_file(fp, part_num=i+1)

        mp.complete_upload()

    else:
        # Single part upload
        k = Key(bucket)
        k.key = key_name
        k.set_contents_from_filename(filename)



def download_from_s3(bucket_name):
    pass


def remove_s3_bucket(bucket_name):
    pass
