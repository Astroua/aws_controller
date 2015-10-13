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


def upload_to_s3(bucket_name, upload_item,
                 create_bucket=False, chunksize=52428800, conn=None,
                 aws_access={}, replace=False):
    '''
    Upload a file or folder to an S3 bucket. Optionally, a new bucket can be
    created. For files larger than 50 Mb (by default), downloads are split
    into chunks. *This requires installing the FileChunkIO library.*

    Folder uploading is modeled from: https://gist.github.com/SavvyGuard/6115006

    Parameters
    ----------
    bucket_name : str
        Name of existing bucket or one to be created.
    upload_iterm : str
        File or folder to be uploaded.
    create_bucket : bool, optional
        Set whether to create a new bucket. An error is raised if the bucket
        already exists.
    chunksize : int, optional
        Size of chunks to split a multi-part upload into. Default to 50 Mb.
    conn : boto.s3.connection.S3Connection, optional
        A connection to S3. Otherwise, one is created.
    aws_access : dict, optional
        Dictionary where AWS_ACCESS_KEY_ID and AWS_ACCESS_KEY_SECRET can be
        given to open a connection. Not needed if your credentials are set
        on your machine.
    replace : bool, optional
        Allow files to be overwritten if the key already exists.
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
            conn = S3Connection()
    else:
        if not isinstance(conn, S3Connection):
            raise TypeError("conn provided is not an S3 Connection.")

    # Check if that bucket exists. Otherwise create a new one if asked for.
    existing_buckets = [b.name for b in conn.get_all_buckets()]
    bucket_exists = True if bucket_name in existing_buckets else False

    if bucket_exists and create_bucket:
        raise Warning("The bucket name given '" + bucket_name +
                      "' already exists.")

    if create_bucket:
        bucket = conn.create_bucket(bucket_name)
    else:
        bucket = conn.get_bucket(bucket_name)

    key_name = upload_item.rstrip("/").split("/")[-1]

    # Now check if the item to upload is a file or folder
    if os.path.isdir(upload_item):
        # Walk through the folder structure.
        for (source_dir, _, filename_list) in os.walk(upload_item):
            for filename in filename_list:
                full_filename = os.path.join(source_dir, filename)

                # Get a key that starts with key_name, but includes the rest of
                # the file structure.
                full_key_path = \
                    source_dir.lstrip(source_dir.split(key_name)[0])
                full_key_name = os.path.join(full_key_path, filename)
                auto_multipart_upload(full_filename, bucket, full_key_name,
                                      replace=replace, chunksize=chunksize)
    elif os.path.isfile(upload_item):
        auto_multipart_upload(upload_item, bucket, key_name, replace=replace,
                              chunksize=chunksize)
    else:
        raise TypeError(upload_item + " is not an existing file or folder."
                        " Check given input.")


def auto_multipart_upload(filename, bucket, key_name, max_size=104857600,
                          chunk_size=52428800, replace=False):
    '''
    Based on the size of the file to be uploaded, automatically partition into
    a multi-part upload.
    '''

    source_size = os.stat(filename).st_size

    # Check if the given key (ie. file or folder name) already exists in
    # the bucket.
    if not replace:
        all_key_names = [k.name for k in bucket.get_all_keys()]
        if key_name in all_key_names:
            raise KeyError(key_name + " already exists in the bucket " +
                           bucket.name + ". Please choose a new key name.")

    if source_size > max_size:
        if NO_CHUNKIO_FLAG:
            raise ImportError("Cannot perform multi-part upload without"
                              " FileChunkIO. Install the package, or increase"
                              " at your own risk.")
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
        k.set_contents_from_filename(filename, replace=replace)


def download_from_s3(filename, key_name, bucket_name, conn=None,
                     aws_access={}):
    '''

    Download a key from a S3 bucket and save to a given file name.

    **Currently only supports one key at a time. This will be extended
    to allow for S3 'folders' to be downloaded.**

    Parameters
    ----------
    filename : str
        Name of output file.
    key_name : str
        Name of key in S3 bucket.
    bucket_name : str
        Name of existing bucket or one to be created.
    conn : boto.s3.connection.S3Connection, optional
        A connection to S3. Otherwise, one is created.
    aws_access : dict, optional
        Dictionary where AWS_ACCESS_KEY_ID and AWS_ACCESS_KEY_SECRET can be
        given to open a connection. Not needed if your credentials are set
        on your machine.
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
            conn = S3Connection()
    else:
        if not isinstance(conn, S3Connection):
            raise TypeError("conn provided is not an S3 Connection.")

    bucket = conn.get_bucket(bucket_name)

    key = bucket.get_key(key_name)

    key.get_contents_to_filename(filename)


def remove_s3_bucket(bucket_name, connection):
    '''
    Delete entire bucket.

    Parameters
    ----------
    key_name : str or list
        Name of key or list of keys in S3 bucket.
    bucket_name : str
        Name of existing bucket or one to be created.
    conn : boto.s3.connection.S3Connection
        A connection to S3.
    '''

    bucket = connection.get_bucket(bucket_name)

    for key in bucket.list():
        key.delete()

    bucket.delete()


def remove_s3_key(key_names, bucket_name, connection):
    '''
    Delete a key or a list of keys in a given bucket.

    Parameters
    ----------
    bucket_name : str
        Name of existing bucket or one to be created.
    conn : boto.s3.connection.S3Connection
        A connection to S3.

    '''

    bucket = connection.get_bucket(bucket_name)

    if isinstance(key_names, list):
        bucket.delete_keys(key_names)
    else:
        bucket.delete_key(key_names)
