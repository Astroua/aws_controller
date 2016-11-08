
'''
Functions for creating temporary IAM credentials attached to single S3 buckets
'''

import boto
import json


def create_s3_creds(proc_name, username, key=None, secret=None):
    '''
    Create temporary S3 credentials with a time-limit to allow users to
    access their analysis products.

    Parameters
    ----------
    proc_name : str
        Name of the process.
    username : str
        Name of the user
    key : str
        Credentials to connect to IAM
    secret : str
        Credentials to connect to IAM
    '''

    # Connect to IAM with boto
    # Try loading credentials in when not given.
    if key is None or secret is None:
        iam = boto.connect_iam()
    else:
        iam = boto.connect_iam(key, secret)

    # Create user. The credentials need to be attached to the process, so
    # combine the username and the proc_name
    cred_user_name = "{0}_{1}".format(username, proc_name)
    user_response = iam.create_user(crepkd_user_name)

    # Create Policy to only allow access to the one S3 bucket
    # The bucket name is assumed to have the same name as the proc_name.
    policy = {}
    policy['Statement'] = \
        [{'Sid': 'AwsIamUserPython',
          'Effect': 'Allow',
          'Action': 's3:*',
          'Resource': ['arn:aws:s3:::{}'.format(proc_name),
                       'arn:aws:s3:::{}/*'.format(proc_name)]}]

    policy_json = json.dumps(policy, indent=2)

    iam.put_user_policy(cred_user_name, 'allow_access_{}'.format(proc_name),
                        policy_json)

    # Generate new access key pair for 'aws-user'
    key_response = \
        iam.create_access_key(cred_user_name)[u'create_access_key_response'][u'create_access_key_result']

    key_id = key_response[u'access_key']['access_key_id']
    key_secret = key_response[u'access_key']['secret_access_key']

    return {"username": cred_user_name, "key_id": key_id,
            "key_secret": key_secret}


def delete_user(username, policy_name=None, key_name=None, iam_connec=None):
    '''
    Deletes IAM user credentials and any associated policy or key names.

    Parameters
    ----------
    username : string
        Name of the user to delete.
    policy_name : string, optional
        Policy attached to the user. All must be deleted before the user can
        be deleted.
    key_name : string, optional
        Name of the access key assigned to the user. All must be deleted before
        the user can be deleted.
    iam_connec : boto.iam.connection.IAMConnection, optional
        Connection to IAM. If None, attempts to create one automatically using
        credentials on the local system.

    Returns
    -------
    True/False : bool
        If True, the user was deleted. If False, some exception was raised
        during the process.
    '''

    if iam_connec is None:
        iam = boto.connect_iam()
    else:
        if not isinstance(iam_connec, boto.iam.connection.IAMConnection):
            raise TypeError("Given iam_connec is not an IAMConnection.")
        iam = iam_connec

    if key_name is not None:
        try:
            iam.delete_access_key(key_name, user_name=username)
        except Exception:
            return False

    if policy_name is not None:
        try:
            iam.delete_user_policy(username, policy_name)
        except Exception:
            return False

    try:
        iam.delete_user(username)
    except Exception:
        return False

    return True
