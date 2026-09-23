from dataclasses import replace
import pytest
from src.climate import load_climate, validate_climate
from src.energy_model import Design,Settings,estimate,compare

@pytest.fixture
def climate(): return load_climate('Abu Dhabi')

def test_identity_and_component_conservation(climate):
 r=compare(climate,Design(),Design(),Settings())
 assert r['saved_kwh']==0
 assert sum(r['baseline']['components'].values())==pytest.approx(r['baseline']['kwh'])

def test_cop_halves_electricity_not_thermal_load(climate):
 a=estimate(climate,settings=Settings(cop=3)); b=estimate(climate,settings=Settings(cop=6))
 assert a['kwh']==pytest.approx(2*b['kwh'])
 assert a['thermal_kwh_per_sqm']==pytest.approx(b['thermal_kwh_per_sqm'])

def test_shading_changes_only_solar(climate):
 a=estimate(climate); b=estimate(climate,Design(shading='Deep'))
 assert b['components']['Solar through glazing']==pytest.approx(a['components']['Solar through glazing']*.6)
 for key in ['Envelope','Air exchange (sensible)','Internal gains']:
  assert a['components'][key]==b['components'][key]

def test_zero_glazing_orientation_invariant(climate):
 assert estimate(climate,Design(wwr=0,orientation='North'))['kwh']==estimate(climate,Design(wwr=0,orientation='West'))['kwh']

def test_equal_glazing_distribution_orientation_invariant(climate):
 a=estimate(climate,Design(dominant_share=.25,orientation='North'))
 b=estimate(climate,Design(dominant_share=.25,orientation='West'))
 assert a['kwh']==pytest.approx(b['kwh'])

def test_insulation_reduces_envelope_only(climate):
 a=estimate(climate); b=estimate(climate,Design(insulation='Improved'))
 assert b['components']['Envelope']<a['components']['Envelope']
 assert b['components']['Solar through glazing']==a['components']['Solar through glazing']

def test_cold_year_zero_cooling(climate):
 cold=climate.copy();cold['t_mean']=5
 assert estimate(cold)['kwh']==0

@pytest.mark.parametrize('settings',[Settings(cop=0),Settings(area=-1),Settings(floors=1.5),Settings(cop=float('nan'))])
def test_invalid_settings_rejected(climate,settings):
 with pytest.raises(ValueError): estimate(climate,settings=settings)

def test_missing_days_rejected(climate):
 with pytest.raises(ValueError): validate_climate(climate.iloc[:-1])

def test_zawaya_directional_plausibility():
 # Owner-supplied comparator; not independent validation, not a tuned target.
 r=compare(load_climate('Cairo'),Design(),Design(orientation='North',shading='Deep',ventilation_credit=.10),Settings())
 assert 0<r['reduction_pct']<100
 assert (625.5-363.2)/625.5*100==pytest.approx(41.93445,abs=.0001)

def test_dominant_glazing_cannot_exceed_facade(climate):
 r=estimate(climate,Design(wwr=.9,dominant_share=1))
 assert r['effective_dominant_share']*r['geometry']['window']<=r['geometry']['facade']/4+1e-9
