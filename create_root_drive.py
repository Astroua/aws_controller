# License under the MIT License - see LICENSE


import boto

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
