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


def user_data(install_casa=True, install_miniconda=False,
              start_flask=False, start_casa=False, casa_version="4.3"):
    '''
    Return a string to be used as the startup script in an instance.

    Parameters
    ----------
    install_casa : bool, optional
        Install CASA on the VM.
    install_miniconda : bool, optional
        Installs a miniconda environment on the VM. Needed to run the
        web-server.
    start_flask : bool, optional
        Start the flask server. NOT YET IMPLEMENTED
    start_casa : bool, optional
        Start a CASA session. NOT YET IMPLEMENTED
    casa_version : str {4.3}, optional
        Version of CASA to install. Currently only 4.3 is supported.
    '''

    if casa_version != "4.3":
        raise TypeError("Only CASA 4.3 is currently supported.")

    if start_flask & start_casa:
        raise UserWarning("Cannot run flask and casa on same instance. "
                          "Run flask on controller instance and casa on "
                          "computing (slave) instances.")

    # The submodule requires some fiddling around, as it is setup to use SSH
    # keys. The extra lines allow use of https instead.
    # http://stackoverflow.com/questions/15674064/github-submodule-access-rights-travis-ci
    run_script = \
        """
        #!/bin/bash

        sudo apt-get update
        sudo apt-get -y install git

        cd $HOME

        mkdir code

        cd $HOME/code

        git clone https://github.com/Astroua/aws_controller.git
        cd aws_controller
        sed -i 's/git@github.com:/https:\/\/github.com\//' .gitmodules
        sed -i 's/git@github.com:/https:\/\/github.com\//' .git/config
        git submodule update --init --recursive

        cd $HOME
        sudo chown -R ubuntu:ubuntu code

        sh $HOME/code/aws_controller/casa-deploy/general-install.sh
        """

    if install_casa:
        casa_install_script = "deploy_casa"+str(casa_version)+".sh"
        run_script = run_script + \
            "sh $HOME/aws_controller/casa-deploy/"+casa_install_script+"\n"
        run_script = run_script + \
            "sh $HOME/aws_controller/casa-deploy/install_casa_pip.sh\n"
        run_script = run_script + \
            "sh $HOME/aws_controller/casa-deploy/install_casa_packages.sh\n"

    if install_miniconda:
        run_script = run_script + \
            "sh $HOME/aws_controller/casa-deploy/install_miniconda.sh\n"

    return run_script
