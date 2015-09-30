# License under the MIT License - see LICENSE


from boto.manage.cmdshell import sshclient_from_instance
import warnings
from datetime import datetime

from launch_instance import launch


def timestring():
    TimeString = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return TimeString


def create_root_drive(name, path_to_key, image_description=None,
                      region='us-west-2',
                      orig_image_id="ami-5189a661",
                      install_kwargs={},
                      verbose=True,
                      auto_terminate=True):
    '''
    Creates the root drive for AstroCompute instances.

    Parameters
    ----------
    name : str
        Name of the image. Note that the time will be appended to the name.
    path_to_key : str
        Path to the key to link to the VM. Note this key must be attached to
        you AWS account.
    image_description : str, optional
        Description of the created image.
    region : str, optional
        Region to create image. orig_image_id must be correct for the region.
    orig_image_id : str, optional
        Image ID to base the new image on. This defaults to ubuntu 14.04.
        Note the ami changes with the chosen region.
    install_kwargs : dict, optional
        Passed to install_packages.
    verbose : bool, optional
        Enables output of the process.
    auto_terminate : bool, optional
        When enabled, terminates the instance after the image has been
        created.
    '''

    key_name = path_to_key.split("/")[-1].rstrip(".pem")

    name += "_"+timestring()

    instance = launch(key_name, region=region, image_id=orig_image_id)

    if verbose:
        print("Instance status: " + str(instance.state))

    try:
        install_packages(instance, path_to_key, verbose=verbose,
                         **install_kwargs)
    except Exception, e:
        warnings.warn("Something went wrong. Terminating instance.")
        instance.terminate()
        raise e

    instance.stop()

    instance.create_image(name, description=image_description, no_reboot=True)

    if not auto_terminate:
        return instance
    else:
        instance.terminate()


def install_packages(instance, path_to_key, install_casa=True,
                     install_miniconda=False,
                     casa_version="4.3", user_name='ubuntu',
                     debug=False, verbose=True):
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
    debug : bool, optional
        Return an interactive shell to test connection before attempting
        installation.
    '''

    if casa_version != "4.3":
        raise TypeError("Only CASA 4.3 is currently supported.")

    # The submodule requires some fiddling around, as it is setup to use SSH
    # keys. The extra lines allow use of https instead.
    # http://stackoverflow.com/questions/15674064/github-submodule-access-rights-travis-ci
    run_script = ["sudo apt-get update", "sudo apt-get -y install git",
                  "git clone https://github.com/Astroua/aws_controller.git",
                  "sed -i 's/git@github.com:/https:\/\/github.com\//' $HOME/aws_controller/.gitmodules",
                  "sed -i 's/git@github.com:/https:\/\/github.com\//' $HOME/aws_controller/.git/config",
                  "git -C $HOME/aws_controller submodule update --init --recursive --force",
                  "sh $HOME/aws_controller/casa-deploy/general_install.sh"]

    if install_casa:
        casa_install_script = "deploy_casa"+str(casa_version)+".sh"
        source_profile = "source .profile"
        run_script.append(source_profile +
                          "&& sh $HOME/aws_controller/casa-deploy/"+casa_install_script)
        run_script.append(source_profile +
                          "&& sh $HOME/aws_controller/casa-deploy/install_casa_pip.sh")
        run_script.append(source_profile +
                          "&& sh $HOME/aws_controller/casa-deploy/install_casa_packages.sh")
        run_script.append(source_profile +
                          "&& sh $HOME/aws_controller/casa-deploy/install_uvmultifit.sh "
                          "$HOME/aws_controller/casa-deploy/external_packages/uvmultifit/")
        run_script.append(source_profile +
                          "&& sh $HOME/aws_controller/casa-deploy/install_casa_analysis_scripts.sh")


    if install_miniconda:
        run_script.append("sh $HOME/aws_controller/casa-deploy/install_miniconda.sh")
        run_script.append(source_profile + "&& conda update --yes conda")

    # Start-up the SSH connection
    ssh_shell = sshclient_from_instance(instance, path_to_key,
                                        user_name=user_name)

    if debug:
        ssh_shell.shell()

    for cmd in run_script:
        status, stdout, stderr = ssh_shell.run(cmd)

        if verbose:
            print("Command: " + cmd)
            print("Status: " + str(status))
            print("Out: " + str(stdout))
            print("Error: " + str(stderr))

        if status != 0:
            print(stderr)
            raise Exception("Failed on " + cmd)
            break

if __name__ == "__main__":

    import sys

    # Call sequence
    # python create_root_drive.py install_casa install_miniconda path_to_key
    # So to create a CASA image:
    # python create_root_drive.py True False /path/to/key.pem

    install_casa = True if sys.argv[1] == "True" else False
    install_miniconda = True if sys.argv[2] == "True" else False
    path_to_key = sys.argv[3]

    if not install_casa and not install_miniconda:
        raise TypeError("Nothing to install! Enable one of CASA or miniconda "
                        " install options on the cmd line.")

    install_kwargs = {}

    if install_casa:
        name = "AstroCompute_UA_CASA_4.3"
        install_kwargs["install_casa"] = True

    if install_miniconda:
        name = "AstroCompute_UA_webserver"
        install_kwargs["install_miniconda"] = True

    if install_miniconda and install_casa:
        name = "AstroCompute_UA_all"

    create_root_drive(name, path_to_key, install_kwargs=install_kwargs)
