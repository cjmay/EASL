
# Efficient Annotation of Scalar Labels (EASL)

[![Travis build status](https://travis-ci.org/cjmay/EASL.svg?branch=master)](https://travis-ci.org/cjmay/EASL)
[![Appveyor build status](https://ci.appveyor.com/api/projects/status/7fy00a0hr7hklxc3/branch/master?svg=true)](https://ci.appveyor.com/project/cjmay/easl/branch/master)

See the [preprint](https://arxiv.org/abs/1806.01170) ([to appear in ACL 2018](https://acl2018.org/programme/papers/)).

- - - 
## Requirements

- Python 3
- The Python packages listed in `requirements.txt` (use `pip install -r requirements.txt` to install them)
- For testing, the Python packages listed in `test-requirements.txt` (use `pip install -r test-requirements.txt` to install them)

## Usage

### Basic usage

We show how to use EASL for one round of annotation on a prepared data set, a collection of sentences we wish to annotate with their political stances (between liberal and conservative).  We have already created a Mechanical Turk HIT layout template (`templates/political/template_political.html`) and a file containing the data set in the format EASL expects (`experiments/political/political.csv`). 
    
1. Prepare the data
    
    Your data should be formatted in a csv file, consisting of (at least) the columns `id, sent`.  For example:

    ```
    id,sent
    1,obama is a legend in his own mind
    2,conservatives are racists
    3,cruz is correct
    4,romney is president
    5,obama thinks there are 57 states
    ```
    
    Note: You can add additional columns. For example, if you want to annotate on a pair of sentences such as premise and hypothesis, the columns will look like `id, premise, hypothesis`.
    
    Let's assume our file name is `experiments/political/political.csv`.
    
    We will run the following to set initial parameters (`alpha, beta, mode, var`).
    
    ```bash
    python scripts/easl-initialize.py experiments/political/political.csv
    ```

    The result csv file (`experiments/political/political_0.csv`) should look similar to the following. 
    
    ```
    id,sent,alpha,beta,mode,var
    1,obama is a legend in his own mind,1,1,0.5,0.0833
    2,conservatives are racists,1,1,0.5,0.0833
    3,cruz is correct,1,1,0.5,0.0833
    4,romney is president,1,1,0.5,0.0833
    5,obama thinks there are 57 states,1,1,0.5,0.0833
    ```
       
    Note that it has additional columns: `alpha, beta, mode, var`.
    
    The HIT layout template is an HTML file that will be interpolated with the values of variables in the HIT batch CSV file (generated in the next step).  To illustrate, Mechanical Turk replaces all instances of the string `${x}` in the template with the entry in column `x` in a given row in the CSV file.  Our layout is located at `templates/political/template_political.html`.
    
    Now, we are ready to start annotation with EASL!

1. Generate HITs

    We generate our HITs by running the following command. 
    
    ```bash
    python scripts/easl-main.py --operation generate --model experiments/political/political_0.csv --hits 25
    ```

    This generates `experiments/political/political_hit_1.csv` that has 25 HITs (and five items per HIT, the default).
    
    The number of HITs (per iteration) should depend on your data size. (See `python scripts/easl-main.py --help` for more details.)
    
1. Publish the HITs (with the template file created earlier).

1. Collect the result and name it `experiments/political/political_result_1.csv`.

1. Update the model

    ```bash
    python scripts/easl-main.py --operation update --model experiments/political/political_0.csv
    ```

    This takes `political_0.csv`, `political_result_1.csv`, and then generates `political_1.csv` (all in the directory `experiments/political/`).
    
1. Go back to the step 2 (Generate HITs). 

    For example, in the next iteration, pass `political_1.csv` to `generate` and `update`; in the subsequent iteration, pass `political_2.csv` to `generate` and `update`.
    
    For convenience, you may use the combined operation `update-generate` to update the model based on HIT results and generate a new batch of HIT data all at once.  For example, the following command updates the model given by `political_0.csv` with the results from `political_result_1.csv` (producing `political_1.csv`) and then generates new batch data `political_hit_2.csv`:

    ```bash
    python scripts/easl-main.py --operation update-generate --model experiments/political/political_0.csv --hits 25
    ```
    
### Automation

Use `easl.mturk.loop` to automate the EASL loop (steps 2 through 6 in the previous section).  For example, the following snippet runs four rounds of EASL on the political data, using HIT type id `ABCDEFG` and HIT layout id `HIJKLMNOP`.  (These identifiers can currently be found by going to the "Create" tab in the Mechanical Turk requester web interface and clicking on the name of an existing project.)

```python
import boto3
from easl.mturk import loop, SANDBOX_ENDPOINT_URL, PRODUCTION_ENDPOINT_URL
import logging

LOGGER = logging.getLogger('mturk')
LOGGER.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)-15s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
LOGGER.addHandler(handler)

# Set endpoint_url=SANDBOX_ENDPOINT_URL for development
client = boto3.client('mturk', endpoint_url=PRODUCTION_ENDPOINT_URL)
loop('experiments/political/political_0.csv',
     {'param_hits': 25},
     'ABCDEFG', 'HIJKLMNOP',
     4, client=client)
```

### Running tests

Use the following snippet to run some tests.

```bash
flake8 && pytest tests
```
