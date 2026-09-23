"""Strict local cache loader. Never fabricates or silently fills climate data."""
import json
import numpy as np
import pandas as pd
from src.config import ROOT, CITIES, YEAR

COLUMNS = ['t_mean','t_max','ghi','north','east','south','west']

def validate_climate(df, year=YEAR):
    expected = pd.date_range(f'{year}-01-01', f'{year}-12-31')
    if not isinstance(df.index, pd.DatetimeIndex) or not df.index.equals(expected):
        raise ValueError('Climate cache must contain exactly one ordered row per day of the requested year.')
    if not set(COLUMNS).issubset(df.columns):
        raise ValueError('Climate cache is missing required columns.')
    if not np.isfinite(df[COLUMNS].to_numpy()).all():
        raise ValueError('Climate cache contains missing or non-finite data.')
    if not df.t_mean.between(-30,60).all() or not df.t_max.between(-30,65).all():
        raise ValueError('Temperature outside accepted screening range.')
    if (df.t_max < df.t_mean).any() or not df.ghi.between(0,15).all():
        raise ValueError('Inconsistent temperature or daily radiation.')
    if (df[['north','east','south','west']] < 0).any().any():
        raise ValueError('Negative facade radiation.')
    return df

def load_climate(city, year=YEAR):
    p = ROOT/'data'/'cache'/f"{CITIES[city]['slug']}_{year}.csv"
    if not p.exists():
        raise FileNotFoundError('No climate cache. Run: python data/fetch_climate.py')
    return validate_climate(pd.read_csv(p,index_col='date',parse_dates=True),year)

def provenance(city, year=YEAR):
    return json.loads((ROOT/'data'/'cache'/f"{CITIES[city]['slug']}_{year}.json").read_text())
