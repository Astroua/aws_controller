
# A few necessary packages
sudo apt-get update
sudo apt-get install -y xorg openbox wget bzip2 ca-certificates git unzip

# Download our repo
git clone https://github.com/Astroua/aws_controller.git
sed -i 's/git@github.com:/https:\/\/github.com\//' $HOME/aws_controller/.gitmodules
sed -i 's/git@github.com:/https:\/\/github.com\//' $HOME/aws_controller/.git/config
git -C $HOME/aws_controller submodule update --init --recursive --force

# Download CASA
wget --quiet https://casa.nrao.edu/download/distro/linux/release/el7/casa-release-4.7.1-el7.tar.gz
tar zxvf casa-release-4.7.1-el7.tar.gz
rm casa-release-4.7.1-el7.tar.gz

# Add CASA to the path
echo 'export PATH=$HOME/casa-release-4.7.1-el7/bin:$PATH' >> $HOME/.profile

sh $HOME/.profile

# Install pip (You'll need to press enter for the first time
# launching CASA)
casa --no-logger --log2term -c "from setuptools.command import easy_install; easy_install.main(['--user', 'pip'])"
# Then install the packages we want
casa --no-logger --log2term -c "import pip; pip.main(['install', 'astropy', '--user']); pip.main(['install', 'astroML', '--user']); pip.main(['install', 'git+https://github.com/PaulHancock/Aegean.git', '--user']); pip.main(['install', 'jdcal', '--user'])"

# Install UVMultiFit
sudo apt-get install libgsl2 libgsl-dev
wget --quiet http://bele.oso.chalmers.se/nordicarc/sw/UVMULTIFIT/UVMULTIFIT_2.2.1-r1.tar.gz
mkdir UVMULTIFIT_2.2.1-r1
tar zxvf UVMULTIFIT_2.2.1-r1.tar.gz -C UVMULTIFIT_2.2.1-r1
rm UVMULTIFIT_2.2.1-r1.tar.gz
cd UVMULTIFIT_2.2.1-r1
python setup.py build_ext --inplace
cd

echo '# UVMULTIFIT' >> $HOME/.casa/init.py
echo 'import sys' >> $HOME/.casa/init.py
echo "sys.path.append('$HOME/UVMULTIFIT_2.2.1-r1/')" >> $HOME/.casa/init.py

# Install CASA utils
wget --quiet ftp://ftp.cv.nrao.edu/pub/casaguides/analysis_scripts.tar
tar xvf analysis_scripts.tar
rm analysis_scripts.tar

echo "# Analysis scripts" >> $HOME/.casa/init.py
echo "sys.path.append('$HOME/analysis_scripts')"  >> $HOME/.casa/init.py
echo "import analysisUtils as au"  >> $HOME/.casa/init.py

# Now install miniconda
wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh
chmod +x miniconda.sh
./miniconda.sh -b
echo "# conda path" >> $HOME/.profile
echo 'export PATH=$HOME/miniconda2/bin:$PATH' >> $HOME/.profile
rm miniconda.sh

sh $HOME/.profile

# Now install the packages we need to be running the process in AWS
conda update --yes conda
conda install --yes boto flask
pip install filechunkio

# Make the download and data products
mkdir data
mkdir data_products
