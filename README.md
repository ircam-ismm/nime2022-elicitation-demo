# rto_nime22

This repository contains some of the code needed to implement the demo (conditionally) accepted at NIME22.
A MAX/MSP patch receives 2D touch data and produce an audio feedback based on the live gesture properties.

The repository is organised as following:

- max: contain the MAX/MSP patch that implement the experiment
- client.py: receive and save the experimental data to file
- data: store experimental data
- notebooks: analysis for experimental data
- viz: live analysis and exploration of experimental data


### Max patch:

1. `python client.py`
1. start the Max patch max/main.maxpat
1. first time only: install all npm dependencies in tab `process` by clicking on all `npm install ...`
1. ..... todo .....

### Visualization of Recorded Data

Some preliminary data (data_29042022_180743.csv) is currently available under data/user.

To test the live visualisation:

1. clone and cd into this repository
1. install a Python (obviously:)) emvironement with `conda env create --file requirements.yaml`
1. activate it with `conda activate rto_nime22`
1. launch the visualisation program with `python viz/app.py`
1. open http://localhost:8050 in a browser
1. drag and drop the csv file into the box

