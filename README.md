# Galaxy tool search test environment

A test harness for playing with the Galaxy tool search backend using Whoosh

## How to use

```
# clone this repo
git clone https://github.com/neoformit/galaxy-tool-search-test.git

# Activate your galaxy virtual env
source $GALAXY_ROOT_PATH/.venv/bin/activate

# Build the test index from json
python search.py --build

# Make a search and show the results
python search.py "genome"
```

Example search output:
```python
# The details field just shows the JSON data for the subject tool
[{'details': {'description': 'predicts on new data using a preffited model',
              'guid': 'toolshed.g2.bx.psu.edu/repos/bgruening/model_prediction/model_prediction/1.0.8.3',
              'help': '**What it does** Given a fitted and new data sets, this '
                      'tool outpus the prediction results on the data sets via '
                      "invoking the estimator's `predict` or `predict_proba` "
                      'method. For estimator, this tool supports fitted '
                      'sklearn estimators (pickled) and trained deep learning '
                      'models (model skeleton + weights). It predicts on three '
                      'different dataset inputs, - tabular - sparse - '
                      'bio-sequences in a fasta file - reference genome and '
                      'variant call file',
              'id': 'model_prediction',
              'name': 'Model Prediction',
              'panel_section_name': 'Machine Learning'},
  'matched_terms': [('help', b'genom')],  # This shows which terms matching to fields
  'score': 1.824578696859119},            # The final score
 
  ...more results
  
]
```

# Using different tool sources

Open `search.py` and point `TOOLS_JSON` to a JSON file containing your tool data. The repo includes two data sources:
- `tools.json` includes over 1000 tools but with no `help` text
- `machine.json` includes 20 samples related to machine learning, of which 5 have help text with some high frequency words 

# Querying the Galaxy index

Connecting is tricky - the schema must match Galaxy's. Edit the `search.py` to point `INDEX_DIR` at the root folder for
Galaxy's "default" index. You can uncomment/edit the existing line to see how this should look. 
