import setuptools
import re
import os

# versioning ------------
VERSIONFILE="slackker/__init__.py"
getversion = re.search( r"^__version__ = ['\"]([^'\"]*)['\"]", open(VERSIONFILE, "rt").read(), re.M)
if getversion:
    new_version = getversion.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

# Setup ------------
def read_file(file_name):
    path = os.path.join(os.path.dirname(__file__), file_name)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

setuptools.setup(
     install_requires=['slack_sdk>=3.19.0','numpy','matplotlib'],
     python_requires='>=3.5',
     name='slackker',
     version=new_version,
     license="Apache-2.0",
     author="Siddhesh Gunjal",
     author_email="siddhu19@live.com",
     description="Python package for reporting your Model training status in realtime on slack channel.",
     long_description=read_file("README.md"),
     long_description_content_type="text/markdown",
     url="https://github.com/siddheshgunjal/slackker",
     packages=setuptools.find_packages(), # Searches throughout all dirs for files to include
     include_package_data=True, # Must be true to include files depicted in MANIFEST.in
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: Apache Software License",
         "Operating System :: OS Independent",
         "Intended Audience :: Developers",
         "Intended Audience :: Information Technology",
         "Intended Audience :: Science/Research",
     ],
 )