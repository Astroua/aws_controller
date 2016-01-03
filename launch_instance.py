# License under the MIT License - see LICENSE

import boto.ec2
import os
import time


def launch(key_name=None, region='us-west-2', image_id='ami-5189a661',
           instance_type='t2.micro', security_groups='launch-wizard-1',
           user_data=None, initial_check=False):
    '''
    '''

    if not isinstance(security_groups, list):
        security_groups = [security_groups]

    ec2 = boto.ec2.connect_to_region(region)

    reserve = ec2.run_instances(image_id, key_name=key_name,
                                instance_type=instance_type,
                                security_groups=security_groups,
                                user_data=user_data)

    inst = reserve.instances[0]

    while inst.state == u'pending':
        time.sleep(10)
        inst.update()

    if initial_check:
        # Wait for the status checks first
        status = ec2.get_all_instance_status(instance_ids=[inst.id])[0]

        check_stat = "Status:initializing"

        while str(status.system_status) == check_stat and str(status.instance_status) == check_stat:
            time.sleep(10)
            status = ec2.get_all_instance_status(instance_ids=[inst.id])[0]

    return inst

    # ec2.get_instance_attribute('i-336b69f6', 'instanceType')
