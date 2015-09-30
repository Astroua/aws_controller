# aws_controller

Basic scripts to automate EC2 instances on AWS. We're radio astronomers, so built-in is the ability to install CASA, along with some add-ons.

**The instructions assume you have your aws credentials configured.**
**Run 'aws configure' to do so.**

Requires
--------
* boto
* paramiko
* awscli

Creating an image
-----------------
An image can be created running ```create_root_drive.py``` by importing into a python session:
```
# Assuming you are in the aws_controller directory
from create_root_drive import create_root_drive
create_root_drive("new_image", "/path/to/key.pem",
                  install_kwargs={"install_casa": True})
```
Or by running from the command line:
```
python create_root_drive.py True False "/path/to/key.pem"
```
These two calls are equivalent, and will install CASA 4.3 on a new image. By default, the original image is ubuntu 14.04 (ami code from us-west-2 or Oregon region).
*Note: A timestamp is attached to the image name provided.*

Developers
----------
* [Eric Koch](@e-koch)
* [Alex Tetarenko](@tetarenk)
* [Greg Sivakoff](@radioastronomer)
* [Erik Rosolowsky](@low-sky)
Support from the SKA AstroCompute Program.
