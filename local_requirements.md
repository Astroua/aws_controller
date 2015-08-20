
Local Tools you need
====================

Boto
----
`pip install boto`
or
`conda install boto`

OR try using the newest version, boto3:
`pip install boto3`

The conversion between the two is given here: `http://boto3.readthedocs.org/en/latest/guide/migrations3.html`__.

awscli
------
`pip install awscli`

Create a credential file at `~/.aws/credentials` that contains:

```
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region=us-west-2
```

The region can be changed, but us-west-2 is probably best for us.




