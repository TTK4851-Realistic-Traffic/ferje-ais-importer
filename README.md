ferje-ais-importer
===



## Local development

The easiest way to test locally is to run the automated tests in `ferjeimporter/tests/main.py`. 
They try to simulate the real environment. Alternatively run your changes locally and push the changes to AWS, 
and see if it works.

We haven't created any scrambled testdata yet. In the mean time will you have to provide your own.

1. Place the files `2018-07-01.csv` and `2018-07-01_shipdata.csv` inside `ferjeimporter/tests/testdata/`.
   You should have gotten these files from the project earlier.
1. Setup a virtual environment in the root of this project
    1. `pip3 install virtualenv`
    1. `virtualenv venv --python=python3.8`
    1. `source ./venv/bin/activate`
       Windows users may have to use another strategy to successfully activate virtual environments 
       https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#activating-a-virtual-environment
    1. `pip3 install -r requirements-frozen.txt`
1. Run the tests through PyCharm, VSCode or terminal (whatever you prefer)

Our Python tests uses the package [moto](https://pypi.org/project/moto/). It simplifies interactions with AWS when running 
tests by simulating an actual environment, but is in reality only run locally. This allows you as developer to interact with AWS as normal, 
using [boto3](https://boto3.amazonaws.com/). See `ferjeimporter/tests/ test_import_success` for a working example. 