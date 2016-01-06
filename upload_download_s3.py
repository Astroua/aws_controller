# License under the MIT License - see LICENSE

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import os
import math
import fnmatch

from utils import timestring

try:
    from filechunkio import FileChunkIO
    NO_CHUNKIO_FLAG = False
except ImportError:
    NO_CHUNKIO_FLAG = True
    Warning("The filechunkio library could not be imported. Uploading large "
            "files will result in an error.")


def upload_to_s3(bucket_name, upload_item,
                 create_bucket=False, chunk_size=52428800, conn=None,
                 aws_access={}, replace=False, key_prefix=None):
    '''
    Upload a file or folder to an S3 bucket. Optionally, a new bucket can be
    created. For files larger than 50 Mb (by default), downloads are split
    into chunks. *This requires installing the FileChunkIO library.*

    Folder uploading is modeled from: https://gist.github.com/SavvyGuard/6115006

    Parameters
    ----------
    bucket_name : str
        Name of existing bucket or one to be created.
    upload_item : str
        File or folder to be uploaded.
    create_bucket : bool, optional
        Set whether to create a new bucket. An error is raised if the bucket
        already exists.
    chunksize : int, optional
        Size of chunks to split a multi-part upload into. Default to 50 Mb.
    conn : boto.s3.connection.S3Connection, optional
        A connection to S3. Otherwise, one is created.
    aws_access : dict, optional
        Dictionary where aws_access_key_id and aws_secret_access_key can be
        given to open a connection. Not needed if your credentials are set
        on your machine.
    replace : bool, optional
        Allow files to be overwritten if the key already exists.
    key_prefix : str, optional
        Add a prefix for the bucket key name.
    '''

    # Create S3 connection if none are given.
    if conn is None:
        if "aws_access_key_id" in aws_access.keys() and "aws_secret_access_key" in aws_access.keys():
            conn = S3Connection(**aws_access)
        elif len(aws_access.keys()) > 0:
            raise KeyError("aws_access must contain 'aws_access_key_id'"
                           " and 'aws_secret_access_key'. All other"
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
                    source_dir.replace(source_dir.split(key_name)[0], "")
                if key_prefix is None:
                    full_key_name = os.path.join(full_key_path, filename)
                else:
                    full_key_name = os.path.join(key_prefix, full_key_path,
                                                 filename)

                auto_multipart_upload(full_filename, bucket, full_key_name,
                                      replace=replace, chunk_size=chunk_size)
    elif os.path.isfile(upload_item):
        if key_prefix is not None:
            key_name = os.path.join(key_prefix, key_name)
        auto_multipart_upload(upload_item, bucket, key_name, replace=replace,
                              chunk_size=chunk_size)
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


def download_from_s3(key_name, bucket_name, conn=None,
                     aws_access={}, output_dir=None):
    '''

    Download a key from a S3 bucket and save to a given file name.

    Parameters
    ----------
    key_name : str
        Name of key in S3 bucket. Supports wildcards for downloading groups or
        "folder" structures in a bucket.
    bucket_name : str
        Name of existing bucket or one to be created.
    conn : boto.s3.connection.S3Connection, optional
        A connection to S3. Otherwise, one is created.
    aws_access : dict, optional
        Dictionary where aws_access_key_id and aws_secret_access_key can be
        given to open a connection. Not needed if your credentials are set
        on your machine.
    output_dir : str
        Path appended to the files downloaded.
    '''

    # Create S3 connection if none are given.
    if conn is None:
        if "aws_access_key_id" in aws_access.keys() and "aws_secret_access_key" in aws_access.keys():
            conn = S3Connection(**aws_access)
        elif len(aws_access.keys()) > 0:
            raise KeyError("aws_access must contain 'aws_access_key_id'"
                           " and 'aws_secret_access_key'. All other"
                           " entries are ignored.")
        else:
            # Use the AWS Keys saved on your machine.
            conn = S3Connection()
    else:
        if not isinstance(conn, S3Connection):
            raise TypeError("conn provided is not an S3 Connection.")

    if output_dir is None:
        output_dir = ""

    bucket = conn.get_bucket(bucket_name)

    if "*" not in key_name:
        key = bucket.get_key(key_name)

        # Strip out preceding directory and leave filename
        out_file = os.path.join(output_dir, key_name.split("/")[-1])

        key.get_contents_to_filename(out_file)
    else:
        all_keys = bucket.get_all_keys()

        for key in all_keys:
            if fnmatch.fnmatchcase(key.name, key_name):
                out_file = os.path.join(output_dir, key.name)

                # Check that the file structure exists. If not, create it.
                folders = out_file.rstrip("/").split("/")[:-1]
                slash_start = 0 if out_file.startswith("/") else 1
                for folder in accumulator(folders, start_space=slash_start):
                    if os.path.isdir(folder):
                        continue
                    os.mkdir(folder)
                key.get_contents_to_filename(out_file)


def remove_s3_bucket(bucket_name, connection):
    '''
    Delete entire bucket.

    Parameters
    ----------
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
    key_name : str or list
        Name of key or list of keys in S3 bucket. Wildcards are also
        supported.
    bucket_name : str
        Name of existing bucket.
    conn : boto.s3.connection.S3Connection
        A connection to S3.

    '''

    bucket = connection.get_bucket(bucket_name)

    if isinstance(key_names, list):
        bucket.delete_keys(key_names)
    elif "*" in key_names:
        all_keys = bucket.get_all_keys()
        for key in all_keys:
            if fnmatch.fnmatchcase(key.name, key_names):
                bucket.delete_key(key.name)
    else:
        bucket.delete_key(key_names)


def accumulator(iterable, typeof=str, spacer="/", start_space=0):
    total = typeof()

    for i, item in enumerate(iterable):
        if i >= start_space:
            total += spacer+item
        else:
            total += item
        yield total
