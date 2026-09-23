"""One-time NASA POWER download. Real daily weather + hourly solar geometry.
Run from repository root: python data/fetch_climate.py --year 2025
No downloads occur when the app starts. No synthetic fallback.
"""
import sys, argparse, json, hashlib
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import numpy as np
import pvlib
from src.config import CITIES, ROOT, YEAR
from src.climate import validate_climate

SESSION=requests.Session()
SESSION.mount('https://', HTTPAdapter(max_retries=Retry(total=3,backoff_factor=1,status_forcelist=[429,500,502,503,504])))

def request(city, year, temporal, parameters):
    c=CITIES[city]
    url=f'https://power.larc.nasa.gov/api/temporal/{temporal}/point'
    response=SESSION.get(url,params={'parameters':parameters,'community':'RE','latitude':c['lat'],'longitude':c['lon'],'start':f'{year}0101','end':f'{year}1231','format':'JSON','time-standard':'UTC'},timeout=120)
    response.raise_for_status()
    payload=response.json()
    df=pd.DataFrame(payload['properties']['parameter'])
    df.index=pd.to_datetime(df.index,format='%Y%m%d' if temporal=='daily' else '%Y%m%d%H')
    df=df.sort_index()
    if not np.isfinite(df.to_numpy()).all() or (df <= -900).any().any():
        raise ValueError(f'{city}: NASA fill/missing values; refusing to cache')
    return df,{'url':response.url,'parameters':payload.get('parameters'),'header':payload.get('header')}

def fetch(city,year):
    daily, dmeta=request(city,year,'daily','T2M,T2M_MAX,ALLSKY_SFC_SW_DWN')
    hourly, hmeta=request(city,year,'hourly','ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DNI,ALLSKY_SFC_SW_DIFF')
    expected=pd.date_range(f'{year}-01-01',f'{year+1}-01-01',freq='h',inclusive='left')
    if not hourly.index.equals(expected): raise ValueError('Incomplete hourly solar year')
    # NASA hourly timestamps denote hourly intervals; midpoint approximates
    # solar position within each interval. pvlib SPA + isotropic sky model.
    times=hourly.index.tz_localize('UTC')+pd.Timedelta(minutes=30)
    c=CITIES[city]
    pos=pvlib.solarposition.get_solarposition(times,c['lat'],c['lon'])
    ghi=hourly.ALLSKY_SFC_SW_DWN.to_numpy()
    dni=hourly.ALLSKY_SFC_SW_DNI.to_numpy()
    dhi=hourly.ALLSKY_SFC_SW_DIFF.to_numpy()
    if (hourly < 0).any().any(): raise ValueError('Negative hourly solar radiation')
    out=daily.rename(columns={'T2M':'t_mean','T2M_MAX':'t_max','ALLSKY_SFC_SW_DWN':'ghi'})
    for name,az in [('north',0),('east',90),('south',180),('west',270)]:
        poa=pvlib.irradiance.get_total_irradiance(90,az,pos.apparent_zenith.to_numpy(),pos.azimuth.to_numpy(),dni,ghi,dhi,albedo=0.20,model='isotropic')['poa_global']
        # 1-hour intervals: W/m² -> kWh/m²/day, no annual multiplier.
        out[name]=pd.Series(poa,index=hourly.index).resample('D').sum()/1000
    validate_climate(out,year)
    cache=ROOT/'data'/'cache'; cache.mkdir(exist_ok=True)
    p=cache/f"{c['slug']}_{year}.csv"
    out.index.name='date'
    data=out.to_csv(float_format='%.6f')
    meta={'city':city,'year':year,'fetched_utc':datetime.now(timezone.utc).isoformat(),'daily':dmeta,'hourly':hmeta,'pvlib_version':pvlib.__version__,'facade_method':'SPA at hourly midpoint; vertical isotropic transposition, ground albedo 0.20','sha256':hashlib.sha256(data.encode()).hexdigest(),'rows':len(out),'august_mean_daily_max_c':float(out.loc[out.index.month==8,'t_max'].mean())}
    # Raw responses are reproducible from URLs; compact daily facade cache is committed.
    p.with_suffix('.csv.tmp').write_text(data); p.with_suffix('.csv.tmp').replace(p)
    p.with_suffix('.json').write_text(json.dumps(meta,indent=2))
    print(city,meta['rows'],'days; August mean daily high',round(meta['august_mean_daily_max_c'],1),'°C',flush=True)
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--year',type=int,default=YEAR); parser.add_argument('--city',choices=list(CITIES)); args=parser.parse_args()
    for city in ([args.city] if args.city else CITIES): fetch(city,args.year)
