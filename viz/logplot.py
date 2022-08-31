#!/sw/bin/python3

logfilename = '/Users/schwarz/Documents/projects/element/research/rto_nime22/elicitation-nime22-project/data/2022-07-28T13-33-17.641Z.txt'

import pandas as pd
df = pd.read_json(logfilename, lines=True)
print (df)

# split into the 4 dataframes by type of line 
datind = df['logtype'] == 'data'
segind = df['logtype'] == 'segment'
evtind = df['logtype'] == 'event'
fbind  = df['logtype'] == 'feedback'

data     = df[datind].dropna(axis=1)
segments = df[segind].dropna(axis=1)
events   = df[evtind].dropna(axis=1)
fb       = df[fbind]   #.dropna(axis=1)
