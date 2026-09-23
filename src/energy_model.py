"""Sensible cooling screening model; all units and assumptions in methodology.md.
No empirical calibration to the owner's benchmark; no arbitrary total-load cuts.
"""
from dataclasses import dataclass, asdict
from math import sqrt, isfinite
import pandas as pd
from src.config import BUILDINGS, INSULATION, SHADING, ORIENTATIONS
from src.climate import load_climate

@dataclass(frozen=True)
class Design:
    wwr: float = .40
    orientation: str = 'West'
    shading: str = 'None'
    insulation: str = 'Legacy / standard'
    # Illustrative double glazing performance, not a product certification.
    window_u: float = 2.8
    shgc: float = .60
    # 70% of glazing faces the dominant direction; remaining 30% split equally.
    dominant_share: float = .70
    # Counterfactual reduction in sensible air-exchange load ONLY; not a
    # recommendation to reduce required outdoor air. Default no credit.
    ventilation_credit: float = 0.

@dataclass(frozen=True)
class Settings:
    area: float = 2000.
    floors: int = 2
    height: float = 3.5
    base_temp: float = 18.
    cop: float = 3.
    ach: float = .50
    internal_w: float = 12.
    hours: float = 12.

    @classmethod
    def for_building(cls,name,**overrides):
        b=BUILDINGS[name]
        return cls(**({k:v for k,v in b.items() if k!='wwr'} | overrides))

def validate(design, s):
    numeric=list(asdict(s).values())+[design.wwr,design.window_u,design.shgc,design.dominant_share,design.ventilation_credit]
    if not all(isfinite(v) for v in numeric): raise ValueError('All inputs must be finite.')
    if s.area<=0 or s.floors<1 or int(s.floors)!=s.floors or s.height<=0 or s.cop<=0: raise ValueError('Invalid area, geometry or COP.')
    if not 0<=s.ach<=10 or not 0<=s.internal_w<=100 or not 0<=s.hours<=24 or not 10<=s.base_temp<=30: raise ValueError('Invalid operating assumptions.')
    if not 0<=design.wwr<=.95 or not 0<=design.shgc<=1 or design.window_u<=0 or not .25<=design.dominant_share<=1 or not 0<=design.ventilation_credit<=.20: raise ValueError('Invalid design assumptions.')
    if design.orientation not in ORIENTATIONS or design.shading not in SHADING or design.insulation not in INSULATION: raise ValueError('Unknown design option.')

def geometry(s,design):
    """Square footprint with equal floor plates; m² of actual treated surface."""
    footprint=s.area/s.floors
    facade=4*sqrt(footprint)*s.height*s.floors
    return {'roof':footprint,'facade':facade,'window':facade*design.wwr,'wall':facade*(1-design.wwr)}

def estimate(climate, design=Design(), settings=Settings()):
    validate(design,settings)
    s=settings; g=geometry(s,design)
    degree_days=(climate.t_mean-s.base_temp).clip(lower=0)
    cooling=(climate.t_mean>s.base_temp).astype(float)
    wall_u,roof_u=INSULATION[design.insulation]
    # Q = UA * degree-hours / 1000. 24 h/day, W->kW. DOE UA principle [R3].
    envelope=(g['wall']*wall_u+g['roof']*roof_u+g['window']*design.window_u)*24*degree_days/1000
    # Facade kWh/m²/day comes from NASA hourly solar + pvlib [R1,R2].
    # A single facade has one quarter of total facade area. Cap allocation
    # so no facade can contain more glazing than its physical area.
    effective_share=min(design.dominant_share, 1/(4*design.wwr)) if design.wwr else design.dominant_share
    shares={name.lower():(effective_share if name==design.orientation else (1-effective_share)/3) for name in ORIENTATIONS}
    radiation=sum(climate[name]*share for name,share in shares.items())
    solar=g['window']*design.shgc*SHADING[design.shading]*radiation*cooling
    # 0.335 Wh/(m³ K) = 1.2 kg/m³ * 1005 J/(kg K) / 3600 J/Wh.
    # Constant dry-air properties; ignores latent heat and air-density variation.
    air=.335*s.ach*s.area*s.height*24*degree_days/1000*(1-design.ventilation_credit)
    # Explicit sensible internal gain scenario on cooling days, W/m² -> kW/m².
    internal=s.internal_w*s.hours*s.area/1000*cooling
    thermal=pd.DataFrame({'Envelope':envelope,'Solar through glazing':solar,'Air exchange (sensible)':air,'Internal gains':internal})
    electrical=thermal/s.cop
    total=float(electrical.to_numpy().sum())
    return {'kwh':total,'kwh_per_sqm':total/s.area,'thermal_kwh_per_sqm':float(thermal.to_numpy().sum())/s.area,'cdd':float(degree_days.sum()),'components':electrical.sum().to_dict(),'monthly':electrical.resample('MS').sum(),'geometry':g,'effective_dominant_share':effective_share}

def compare(climate, baseline, proposed, settings):
    b=estimate(climate,baseline,settings); p=estimate(climate,proposed,settings)
    saving=b['kwh']-p['kwh']
    return {'baseline':b,'proposed':p,'saved_kwh':saving,'reduction_pct':100*saving/b['kwh'] if b['kwh']>0 else 0.}

def estimate_cooling_load(city,building_type,interventions=None):
    """Convenience API returning cooling electricity kWh/m²/year."""
    design=Design(**({'wwr':BUILDINGS[building_type]['wwr']} | (interventions or {})))
    return estimate(load_climate(city),design,Settings.for_building(building_type))['kwh_per_sqm']
