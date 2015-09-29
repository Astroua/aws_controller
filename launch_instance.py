# License under the MIT License - see LICENSE

import boto.ec2
import os
import time


def launch(key_name, region='us-west-2', image_id='ami-5189a661',
           instance_type='t2.micro', group_names='launch-wizard-1',
           install_packages=False, kwargs={}):
    '''
    '''

    if install_packages:
        myuserdata = user_data(**kwargs)
    else:
        myuserdata = None

    if not isinstance(group_names, list):
        group_names = [group_names]

    ec2 = boto.ec2.connect_to_region(region)

    reserve = ec2.run_instances(image_id, key_name=key_name,
                                instance_type=instance_type,
                                user_data=myuserdata, group_names=group_names)

    inst = reserve.instances[0]

    while inst.state == u'pending':
        time.sleep(10)
        inst.update()

    return inst

    # ec2.get_instance_attribute('i-336b69f6', 'instanceType')
