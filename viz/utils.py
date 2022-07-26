import numpy as np
import pandas as pd

import seaborn as sns
tab10 = sns.color_palette('tab10')

import sklearn.preprocessing as skprep


################################################################################
# Serialisation
def mms_to_json(model):
    serialize = json.dumps

    data = {}
    data['init_params'] = model.get_params()
    data['model_params'] = mp = {}
    for p in ('min_', 'scale_','data_min_', 'data_max_', 'data_range_'):
        mp[p] = getattr(model, p).tolist()
    return serialize(data)

def mms_from_json(jstring):
    data = json.loads(jstring)
    model = skprep.MinMaxScaler(**data['init_params'])
    for name, p in data['model_params'].items():
        setattr(model, name, np.array(p))
    return model


################################################################################
# data file processing
def select_active_dfs(dfs, register):
    data_df = pd.DataFrame()
    for active in register['active']:
        df = dfs[active]
        df['card_id'] = str(active)
        data_df = pd.concat([data_df, df])
    return data_df

def format_from_json(json, source='/data'):
    df = pd.read_json(json, orient='split')
    df.columns = [0, 'source', 'data']
    return format_from_df(df, source=source)

def format_from_df(df,  source='/data'):
    data_mask = ~df['timestamp'].isna()
    columns = [
    'sample_key', 'timestamp0', 'timestamp',
    'stroke_id', 'segment_id',
    'x', 'y', 'p', 'x_', 'y_', 'p_', 'x0', 'y0', 'p0', 'x1', 'y1',
    's', 'angle', 'dangle', 'input', 'audio'
    ]
    data_df = df[data_mask][columns]
    return data_df

def format_data(df):
    new_rows = []
    for i, row in df.iterrows():
        row = eval(row['data'])
        new_rows.append(row)
    data = pd.DataFrame(data=new_rows)

    mms = skprep.MinMaxScaler()
    data['timestamp0_norm'] = mms.fit_transform(data['timestamp0'].values.reshape(-1, 1)).reshape(-1)
    
    return data


################################################################################
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
