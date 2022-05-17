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
    select_df = select(df, source=source)
    if source == '/data':
        data_df = format_data(select_df)
    elif source == '/feat':
        data_df = format_feat(select_df)
    return data_df

def format_data(df):
    new_rows = []
    default_value = np.ones(3) * np.nan

    for i, row in df.iterrows():

        row = eval(row['data'].replace('false', 'False'))

        try:
            key = row['sample_key']
            t0 = row['timestamp0']
            t0_norm = 0
            ts = row['timestamp']
            stroke_id = row['stroke_id']
            segment_id = row['segment_id']

            x, y, p = row.get('xyp', default_value)
            x_, y_, p_ = row.get('rel_xyp', default_value)
            x0, y0, p0 = row.get('rel_xyp_lp', default_value)
            # x1, y1, p1 = row.get('xyp_sg', default_value)
            s = row['s']
            x1, y1 = row['dx_dy']
            angle = row['angle']
            # da = row['da']
            # da = da[0] if isinstance(da, (list,)) else da

            new_row = [key, t0, t0_norm, ts, 
                       stroke_id, segment_id, 
                       x, y, p, x_, y_, p_, 
                       x0, y0, p0, x1, y1,
                       s, angle]

            new_rows.append(new_row)
        except KeyError as error:
            print("KeyError", i, row)

    data = pd.DataFrame(data=new_rows,
                        columns=['key', 't0', 't0_norm', 'ts',
                                 'stroke_id', 'segment_id',
                                 'x', 'y', 'p', 'x_', 'y_', 'p_',
                                 'x0', 'y0', 'p0', 'x1', 'y1',
                                 's', 'angle']
                       )
    mms = skprep.MinMaxScaler()
    data['t0_norm'] = mms.fit_transform(data['t0'].values.reshape(-1, 1)).reshape(-1)
    
    return data

# def format_feat(df):
#     # feat = feat['1'].str.replace('null', '0')??
#     new_rows = []
#     for i, row in df.iterrows():
#         row = eval(row['data'])
#         key = row['sample_key']
#         segment_id = row['segment_id']
#         s = row['s']
#         # in case da does not exist
#         da = row.get('da', 0)
#         min_dtw = row.get('min_dtw', -1)
#         min_dtw_id = row.get('min_dtw_id', -1)

#         new_row = [key, segment_id, s, da, min_dtw, min_dtw_id]
#         new_rows.append(new_row)

#     data = pd.DataFrame(data=new_rows,
#                         columns=['key', 'segment_id', 's', 'da', 'min_dtw', 'min_dtw_id'])
#     return data


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


