
import seaborn as sns
tab10 = sns.color_palette('tab10')

################################################################################
# data file processing

import numpy as np
import pandas as pd

def format_from_json(jsonified_cleaned_data, source='/data'):
    data = pd.read_json(jsonified_cleaned_data, orient='split')
    data.columns = [0, 'source', 'data']
    select_df = select(data, source=source)

    if source == '/data':
        data_df = format_data(select_df)
    elif source == '/feat':
        data_df = format_feat(select_df)

    return data_df

def format_data(df):
    new_rows = []
    default_value = np.ones(3) * np.nan

    for i, row in df.iterrows():

        row = eval(row['data'].replace("false", "False"))

        key = row['sample_key']
        t0 = row['timestamp0']
        ts = row['timestamp']
        stroke_id = row['stroke_id']

        x, y, p = row.get('xyp', default_value)
        x_, y_, p_ = row.get('rel_xyp', default_value)
        x0, y0, p0 = row.get('rel_xyp_lp', default_value)
        x1, y1, p1 = row.get('xyp_sg', default_value)

        new_row = [key, t0, ts, stroke_id, x, y, p, x_, y_, p_, x0, y0, p0, x1, y1, p1]
        new_rows.append(new_row)

    data = pd.DataFrame(data=new_rows,
                        columns=['key', 't0', 'ts', 'stroke_id',
                                 'x', 'y', 'p', 'x_', 'y_', 'p_',
                                 'x0', 'y0', 'p0', 'x1', 'y1', 'p1']
                       )

    return data

def format_feat(df):
    # feat = feat['1'].str.replace('null', '0')??
    new_rows = []
    for i, row in df.iterrows():
        row = eval(row['data'])
        key = row['sample_key']
        segment_id = row['segment_id']
        s = row['s']
        # in case da does not exist
        da = row.get('da', 0)
        min_dtw = row.get('min_dtw', -1)
        min_dtw_id = row.get('min_dtw_id', -1)

        new_row = [key, segment_id, s, da, min_dtw, min_dtw_id]
        new_rows.append(new_row)

    data = pd.DataFrame(data=new_rows,
                        columns=['key', 'segment_id', 's', 'da', 'min_dtw', 'min_dtw_id'])
    # data = data.convert_dtypes()
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


