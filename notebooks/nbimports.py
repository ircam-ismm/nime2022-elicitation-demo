import sys, os
from importlib import reload
# from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
import numpy as np
import pandas as pd

import scipy.signal as scsig

tab10 = sns.color_palette('tab10')

# import sklearn.preprocessing as skprep
# import scipy.stats as sstat
# import pingouin as pg

# load the app located in ../src
# USER_HOME = Path.home()
# RTO_ROOT = "Documents/research/rto/src/"
# sys.path.append(os.path.join(USER_HOME, RTO_ROOT))

# pandas select
from functools import reduce
from operator import and_, or_
def select(df, **kwargs):
    '''Builds a boolean array where columns indicated by keys in kwargs are tested for equality to their values.
    In the case where a value is a list, a logical or is performed between the list of resulting boolean arrays.
    Finally, a logical and is performed between all boolean arrays.
    '''
    res = []

    for k, v in kwargs.items():
        # several values for multiple column selection
        if isinstance(v, list):
            res_or = []
            for w in v:
                res_or.append(df[k] == w)
            res_or = reduce(lambda x, y: or_(x,y), res_or)
            res.append(res_or)
        # single column selection
        else:
            res.append(df[k] == v)

    # logical and
    if res:
        res = reduce(lambda x, y: and_(x,y), res)
        res = df[res]
    else:
        res = df

    return res
