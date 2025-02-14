#!/bin/bash

#############################
# CONFIGURATION
#############################
# Debug option for py2app, if needed
export DISTUTILS_DEBUG=0
export PYTHON_FOLDER=$HOME/Contents/Resources
export PYTHONEXE=$PYTHON_FOLDER/bin/python
#############################
# PREPARATION
#############################
cd ${GITHUB_WORKSPACE} || exit

export MDANSE_APP_DIR=${CI_TEMP_DIR}/dist/MDANSE.app

export PYTHONPATH=${CI_TEMP_INSTALL_DIR}/lib/python2.7/site-packages:${PYTHONPATH}

# Build API
sudo install_name_tool -change /Users/runner/hostedtoolcache/Python/2.7.18/x64/lib/libpython2.7.dylib /Users/runner/Contents/Resources/lib/libpython2.7.dylib /Users/runner/Contents/Resources/bin/python2.7
sudo install_name_tool -change /Users/runner/hostedtoolcache/Python/2.7.18/x64/lib/libpython2.7.dylib /Users/runner/Contents/Resources/lib/libpython2.7.dylib /Users/runner/Contents/Resources/bin/python
export MACOSX_DEPLOYMENT_TARGET=10.9
sudo ${PYTHONEXE} -m pip install sphinx==1.6.7 stdeb docutils==0.17.1 graphviz
sudo ${PYTHONEXE} setup.py build build_api build_help install

status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to build MDANSE Documentation""${NORMAL}"
	exit $status
fi

# Create directories
mkdir -p ${MDANSE_APP_DIR}/Contents/Resources/bin
mkdir -p ${MDANSE_APP_DIR}/Contents/MacOS
mkdir -p ${MDANSE_APP_DIR}/Contents/Frameworks
#############################
# PACKAGING
#############################
echo -e "${BLUE}""Packaging MDANSE""${NORMAL}"
MDANSE_DMG=MDANSE-${VERSION_NAME}-${DISTRO}-${ARCH}.dmg

#Install py2app
sudo ${PYTHONEXE} -m pip install py2app==0.26.1

# Replace buggy py2app files
echo "Replacing buggy python2 files"
sudo cp -fv "$GITHUB_WORKSPACE/BuildServer/Unix/MacOS/py2app/qt5.py" "$PYTHON_FOLDER/lib/python2.7/site-packages/py2app/recipes"
sudo cp -fv "$GITHUB_WORKSPACE/BuildServer/Unix/MacOS/py2app/qt6.py" "$PYTHON_FOLDER/lib/python2.7/site-packages/py2app/recipes"

echo "Uninstall sphinx and its dependencies"
sudo ${PYTHONEXE} -m pip uninstall -y sphinx Jinja2 MarkupSafe Pygments alabaster babel chardet colorama docutils idna imagesize requests snowballstemmer sphinxcontrib-websupport typing urllib3 graphviz

echo "Building mdanse app"
cd "${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS" || exit
sudo ${PYTHONEXE} build.py py2app --argv-inject "$GITHUB_WORKSPACE" --argv-inject "$VERSION_NAME" --argv-inject "$CI_TEMP_BUILD_DIR" --argv-inject "$CI_TEMP_DIR"
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Cannot build app.""${NORMAL}"
	exit $status
fi

# Add MDANSE version file (should read the version from the bundle with pyobjc, but will figure that out later)
echo "Add mdanse version file"
echo "${VERSION_NAME}" | sudo tee "${MDANSE_APP_DIR}/Contents/Resources/version"

# Copy over instruction for using bundled python
sudo cp -fv "$GITHUB_WORKSPACE/BuildServer/Unix/MacOS/Resources/How to use the bundled python.txt" "$MDANSE_APP_DIR/Contents/MacOS"

#############################
# Copying Python
#############################
### When launching the bundle, the executable target (i.e. MDANSE) modify the python that is shipped with the bundle (si.e. package path, dylib dependencies ...)
### see http://joaoventura.net/blog/2016/embeddable-python-osx/ for technical details
### In our case we also want the user to be able to start directly python without launching the bundle executable (e.g. to run scripts in command line) which is the reason
### why we have to modify the python executable appropriately with the following commands
echo -e "${BLUE}""Copying python""${NORMAL}"
sudo mkdir -p ${MDANSE_APP_DIR}/Contents/Resources/bin

echo "Copy lib"
sudo cp -rv $PYTHON_FOLDER/lib ${MDANSE_APP_DIR}/Contents/Resources

echo "Copy dependency dylibs"
sudo mv -v ${MDANSE_APP_DIR}/Contents/Resources/lib/lib* ${MDANSE_APP_DIR}/Contents/Frameworks
sudo cp /usr/local/lib/libint*.dylib ${MDANSE_APP_DIR}/Contents/Frameworks

# It is necessary to interlink the following dylibs for them to work properly
echo "Change dylib links"
sudo install_name_tool -change /Users/runner/hostedtoolcache/Python/2.7.18/x64/lib/libpython2.7.dylib @executable_path/../Frameworks/libpython2.7.dylib ${MDANSE_APP_DIR}/Contents/MacOS/python
# libpython
sudo install_name_tool -id @executable_path/../Frameworks/libpython2.7.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libpython2.7.dylib
sudo install_name_tool -change /usr/local/opt/gettext/lib/libintl.8.dylib @executable_path/../Frameworks/libintl.8.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libpython2.7.dylib
sudo install_name_tool -change /Users/runner/hostedtoolcache/Python/2.7.18/x64/lib/libpython2.7.dylib  @executable_path/../Frameworks/libpython2.7.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libpython2.7.dylib
# libintl
sudo install_name_tool -change /usr/local/opt/gettext/lib/libintl.8.dylib @executable_path/../Frameworks/libintl.8.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libintl.8.dylib
sudo install_name_tool -change /usr/lib/libiconv.2.dylib @executable_path/../Frameworks/libiconv.2.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libintl.8.dylib
# hashlib
sudo install_name_tool -change /usr/local/opt/openssl@1.1/lib/libssl.1.1.dylib @executable_path/../Frameworks/libssl.1.1.dylib ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/lib-dynload/_hashlib.so
sudo install_name_tool -change /usr/local/opt/openssl@1.1/lib/libcrypto.1.1.dylib @executable_path/../Frameworks/libcrypto.1.1.dylib ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/lib-dynload/_hashlib.so
# libnetcdf
sudo install_name_tool -change @rpath/libnetcdf.13.dylib @executable_path/../Frameworks/libnetcdf.13.dylib ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/netCDF4/_netCDF4.so
sudo install_name_tool -change @rpath/libhdf5.103.dylib @executable_path/../Frameworks/libhdf5.103.dylib ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/netCDF4/_netCDF4.so
sudo install_name_tool -change @rpath/libnetcdf.13.dylib @executable_path/../Frameworks/libnetcdf.13.dylib ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/netCDF4/_netCDF4.so
sudo install_name_tool -change @rpath/libhdf5.103.dylib @executable_path/../Frameworks/libhdf5.103.dylib ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/netCDF4/_netCDF4.so

echo "Copy site.py"
sudo cp ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/site.py ${MDANSE_APP_DIR}/Contents/Resources/.
sudo cp ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/site.py ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/.

echo -e "${BLUE}""Changing wx and vtk dylib links""${NORMAL}"
chmod 777 ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/change_dylib_path.sh
"${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/change_dylib_path.sh"

# Comment out the 'add_system_python_extras' call that add some System path to the sys.path and
# '_boot_multiprocessing' which is bugged since python 2 doesn't have the functions it uses
echo "Replace __boot__.py"
sudo cp -fv ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/__boot__.py ${MDANSE_APP_DIR}/Contents/Resources
echo "./python2 ../Resources/mdanse_gui"  | sudo tee  ${MDANSE_APP_DIR}/Contents/MacOS/launch_mdanse
sudo chmod 755 ${MDANSE_APP_DIR}/Contents/MacOS/launch_mdanse

# Create a bash script that will run the bundled python with $PYTHONHOME set
echo "#!/bin/bash" > ~/python2
{
echo 'SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"'
echo 'PARENT_DIR="$(dirname "$SCRIPT_DIR")"'
echo 'export PYTHONHOME=$PARENT_DIR:$PARENT_DIR/Resources'
echo 'export PYTHONPATH=$PARENT_DIR/Resources/lib/python2.7:$PARENT_DIR/Resources:$PARENT_DIR/Resources/lib/python2.7/site-packages'
echo '$SCRIPT_DIR/python "${@:1}"'
} >> ~/python2
sudo cp -v ~/python2 "${MDANSE_APP_DIR}/Contents/MacOS"
sudo chmod 755 "${MDANSE_APP_DIR}/Contents/MacOS/python2"

#############################
# Cleanup
#############################
# Removing matplotlib/tests ==> 45.2 Mb
echo "Remove files"
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/matplotlib/tests
# Sample data for matplotlib is useless
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/matplotlib/mpl-data/sample_data
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/mpl-data/sample_data
# Scipy package is useless
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/scipy
# ZMQ package is useless
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/zmq
# Remove python
sudo rm -rf $HOME/Contents
#Remove py2app
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/py2app

sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/conf_
#############################
# Create DMG
#############################
sleep 5
echo "Create dmg"
"$GITHUB_WORKSPACE/BuildServer/Unix/MacOS/create-dmg" --background "${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/Resources/dmg/dmg_background.jpg" --volname "MDANSE" --window-pos 200 120 --window-size 800 400 --icon MDANSE.app 200 190 --hide-extension MDANSE.app --app-drop-link 600 185 "${MDANSE_DMG}" ${CI_TEMP_DIR}/dist
sudo mv ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/${MDANSE_DMG} ${GITHUB_WORKSPACE}