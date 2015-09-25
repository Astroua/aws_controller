# License under the MIT License - see LICENSE

import boto
import os


def launch(key_name, region='us-west-2', image_id='ami-5189a661',
           instance_type='t2.micro', install_packages=False, kwargs={}):
    '''
    '''

    if install_packages:
        myuserdata = user_data(**kwargs)
    else:
        myuserdata = None

    ec2 = boto.ec2.connect_to_region(region)

    ec2.run_instances(image_id, key_name=key_name, instance_type=instance_type,
                      user_data=myuserdata)

    return ec2

    # ec2.get_instance_attribute('i-336b69f6', 'instanceType')


def user_data(install_casa=True, install_miniconda=False,
              start_flask=False, start_casa=False):
    '''
    Return a string to be used as the startup script in an instance.
    '''

    if start_flask & start_casa:
        raise UserWarning("Cannot run flask and casa on same instance. "
                          "Run flask on controller instance and casa on "
                          "computing (slave) instances.")

    run_script = \
        """
        #!/bin/bash

        sudo apt-get update
        sudo apt-get install git

        cd $HOME

        mkdir code

        cd $HOME/code

        git clone https://github.com/Astroua/aws_controller.git

        sh $HOME/aws_controller/casa-deploy/general-install.sh
        """

    if install_casa:
        run_script = run_script + \
            "sh $HOME/aws_controller/casa-deploy/deploy_casa4.3.sh\n"

    if install_miniconda:
        run_script = run_script + \
            "sh $HOME/aws_controller/casa-deploy/install_miniconda.sh\n"

    return run_script
