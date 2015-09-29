# License under the MIT License - see LICENSE


from boto.manage.cmdshell import sshclient_from_instance

from launch_instance import launch


def create_root_drive(name, region='us-west-2', key_name='admin_root_maker',
                      orig_image_id="ami-5189a661"):
    '''
    Creates the root drive for AstroCompute instances.
    '''

    kwargs = {"install_casa": True,
              "install_miniconda": True}

    instance = launch(key_name, region=region, image_id=orig_image_id,
                      install_packages=True, kwargs=kwargs)


def install_packages(instance, path_to_key, install_casa=True,
                     install_miniconda=False,
                     casa_version="4.3", user_name='ubuntu'):
    '''
    Install packages in a running instance.

    Requires paramiko for the SSH connection.

    Parameters
    ----------
    instance : Running instance object
        A running instance.
    path_to_key : str
        Path to the SSH key attached to the instance.
    install_casa : bool, optional
        Install CASA on the VM.
    install_miniconda : bool, optional
        Installs a miniconda environment on the VM. Needed to run the
        web-server.
    casa_version : str {4.3}, optional
        Version of CASA to install. Currently only 4.3 is supported.
    '''

    if casa_version != "4.3":
        raise TypeError("Only CASA 4.3 is currently supported.")

    # The submodule requires some fiddling around, as it is setup to use SSH
    # keys. The extra lines allow use of https instead.
    # http://stackoverflow.com/questions/15674064/github-submodule-access-rights-travis-ci
    run_script =["apt-get update", "apt-get -y install git", "cd $HOME",
                 "git clone https://github.com/Astroua/aws_controller.git",
                 "cd aws_controller",
                 "sed -i 's/git@github.com:/https:\/\/github.com\//' .gitmodules",
                 "sed -i 's/git@github.com:/https:\/\/github.com\//' .git/config",
                 "git submodule update --init --recursive",
                 "cd $HOME",
                 "sh $HOME/code/aws_controller/casa-deploy/general_install.sh"]

    if install_casa:
        casa_install_script = "deploy_casa"+str(casa_version)+".sh"
        run_script = run_script + \
            "sh $HOME/aws_controller/casa-deploy/"+casa_install_script
        run_script = run_script + \
            "sh $HOME/aws_controller/casa-deploy/install_casa_pip.sh"
        run_script = run_script + \
            "sh $HOME/aws_controller/casa-deploy/install_casa_packages.sh"

    if install_miniconda:
        run_script = run_script + \
            "sh $HOME/aws_controller/casa-deploy/install_miniconda.sh"

    # Start-up the SSH connection
    ssh_shell = sshclient_from_instance(instance, path_to_key,
                                        user_name=user_name)

    for cmd in run_script:
        try:
            ssh_shell.run(cmd)
        except Exception, e:
            raise e
            break
