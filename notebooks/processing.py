import numpy as np
import pandas as pd

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
    # data['key'] = data
    return data

def format_feat(df):
    # feat = feat['1'].str.replace('null', '0')??
    new_rows = []
    for i, row in df.iterrows():
        row = eval(row['data'])
        key = row['sample_key']
        segment_id = row['segment_id']
        s = row['s']
        da = row.get('da', 0)
        min_dtw = row.get('min_dtw', -1)
        min_dtw_id = row.get('min_dtw_id', -1)
        
        new_row = [key, segment_id, s, da, min_dtw, min_dtw_id]
        new_rows.append(new_row)

    data = pd.DataFrame(data=new_rows, 
                        columns=['key', 'segment_id', 's', 'da', 'min_dtw', 'min_dtw_id'])
    # data = data.convert_dtypes()
    return data


class FeatureExtractor():
    """Computes features, e.g. radius of curvature k and norm of speed s.
    Performs savgol filtering to extract derivatives of input dimensions.
    Assumes evenly sampled time series, presented as a dataframe with columns t, x, y.
    Returns a dataframe with columns t, x, y, x1, x2, y1, y2, k, r, s, a.
    """
    def __init__(self, wl=7, po=2, dims=['c', 's']):
        """
        Args:
            wl: window length
            po: polynom order
        """
        self.wl = wl
        self.po = po
        self.dims = dims

    def __call__(self, sample):
        """Input columns are t, x, y.
        """
        # 1st and 2nd derivatives of position
        savgol_dict = {'window_length':self.wl, 'polyorder':self.po, 'mode':'nearest'}
        for col in sample.columns[1:]:
            sample[col+'1'] = scsig.savgol_filter(sample[col], deriv=1, **savgol_dict)
            sample[col+'2'] = scsig.savgol_filter(sample[col], deriv=2, **savgol_dict)

        # features: c - curvature, s - speed, a - alpha
        a = np.abs(sample['x1']*sample['y2'] - sample['x2']*sample['y1'])
        b = (sample['x1']**2 + sample['y1']**2)**(3/2)
        # log transform for the curvature - should be closer to normal dist
        SMALL = np.finfo(float).eps
        sample['c'] = np.log(1+ a / b + SMALL)
        sample['r'] = np.clip(1/sample['c'], 0, 1e3) / 1e3

        sample['s'] = np.linalg.norm(sample[['x1', 'y1']], axis=1)

        alpha = np.arctan2(sample['y1'], sample['x1'])
        sample['a'] = np.unwrap(alpha, period=np.pi)
        sample['da'] = scsig.savgol_filter(sample['a'], deriv=1, **savgol_dict) * 10

        return sample[self.dims]
