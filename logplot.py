#!/sw/bin/python3

logfilename = '/Users/schwarz/Documents/projects/element/research/rto_nime22/elicitation-nime22-project/data/2022-07-01T19-29-51.584Z.txt'

import pandas as pd
df = pd.read_json(logfilename, lines=True)
print (df)

# split into 3 dataframes by type of line 
datind = df['sample_key'].notnull()
segind = df['min_dtw'].notnull()
evtind = df['event'].notnull()

data     = df[datind].dropna(axis=1)
segments = df[segind].dropna(axis=1)
events   = df[evtind].dropna(axis=1)
