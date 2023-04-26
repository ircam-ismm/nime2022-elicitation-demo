# NIME2022 - Elicitation Demo

This repository contains some of the code needed to implement the demo accepted at NIME22.
A MAX/MSP patch receives 2D touch data and produces an audio feedback based on live gesture properties.

The repository is organised as following:

- elicitation-nime22-project: contain the MAX/MSP project that implement the experiment
- client.py: receive and save the experimental data to file
- data: store experimental data
- viz: live analysis and exploration of experimental data

### Max patch:

1. start the Max patch elicitation-nime22-project.maxproj
2. first time only: install all npm dependencies in tab `process` by clicking on all `npm install ...`
3. download the audio models from [link](https://nubo.ircam.fr/index.php/s/rC5rt5qG8GqswEb/download), courtesy of [ACIDS-Ircam](http://acids.ircam.fr) and Antoine Caillon, and place engine.ts under `other` in the max project.


### Visualization of Recorded Data

Some preliminary data, stored as csv files, is currently available under data/user.

To use the live visualisation:

1. clone and cd into this repository
2. install a Python environement with `conda env create --file requirements.yaml`
3. activate it with `conda activate rto_nime22`
4. launch the visualisation program with `python viz/app.py`
5. open http://localhost:8050 in a browser
6. drag and drop the csv file into the box

### Data Analysis

1. go to dir `notebooks`, start jupyter-lab
2. run `create_dataset` to compile `user_data` into `pilot_0.csv`, `pilot_1.csv`
2. then run `pilot_data` to analyse data and produce plots
