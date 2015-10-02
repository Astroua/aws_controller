
# Install CASA environment and other packages

source .profile

casa_version=${1}

sh $HOME/aws_controller/casa-deploy/deploy_casa${casa_version}.sh

sh $HOME/aws_controller/casa-deploy/install_casa_pip.sh

sh $HOME/aws_controller/casa-deploy/install_casa_packages.sh

sh $HOME/aws_controller/casa-deploy/install_uvmultifit.sh $HOME/aws_controller/casa-deploy/external_packages/uvmultifit/

sh $HOME/aws_controller/casa-deploy/install_casa_analysis_scripts.sh
