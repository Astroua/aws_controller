# License under the MIT License - see LICENSE

import boto


def launch(key_name, region='us-west-2', image_id='ami-5189a661',
           instance_type='t2.micro'):
    '''
    '''

    ec2 = boto.ec2.connect_to_region(region)

    ec2.run_instances(image_id, key_name=key_name, instance_type=instance_type)

    return ec2

    # ec2.get_instance_attribute('i-336b69f6', 'instanceType')
