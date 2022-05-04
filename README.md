# rto_nime22

This repository contains some of the code needed to implement the demo (conditionally) accepted at NIME22.
A MAX/MSP patch receives 2D touch data and produce an audio feedback based on the live gesture properties.

The repository is organised as following:

- max: contain the MAX/MSP patch that implement the experiment
- client.py: receive and save the experimental data to file
- data: store experimental data
- notebooks: analysis for experimental data
- viz: live analysis and exploration of experimental data

Some preliminary data (data_29042022_180743.csv) is currently available under data/user.

To test the live visualisation:
1. install a Python (obviously:)) emvironement with `conda env create --file requirements.yaml`
2. activate it with `conda activate rto_nime22`
3. launch the visualisation program with `python viz/app.py`
4. drag and drop the csv file in the box
