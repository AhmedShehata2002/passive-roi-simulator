import pytest
from src.financial_model import investment_case,intervention_costs
from src.energy_model import Design,Settings

def test_hand_calculation():
 r=investment_case(1000,1,1000,years=2,discount_rate=.1)
 assert r['npv']==pytest.approx(-1000+1000/1.1+1000/1.1**2)
 assert r['payback_years']==1
 assert r['cumulative']==[-1000,0,1000]
 assert r['cumulative_discounted'][-1]==pytest.approx(r['npv'])

def test_zero_discount():
 assert investment_case(1000,1,5000,10,0)['npv']==5000

@pytest.mark.parametrize('saved',[0,-100])
def test_no_payback(saved):
 assert investment_case(saved,1,1000)['payback_years'] is None

def test_free_intervention():
 assert investment_case(100,1,0)['payback_years']==0

def test_maintenance_can_eliminate_savings():
 assert investment_case(100,1,500,annual_maintenance=120)['payback_years'] is None

@pytest.mark.parametrize('kwargs',[{'capex':-1},{'discount_rate':-.1},{'years':1.5},{'tariff':float('nan')}])
def test_invalid_rejected(kwargs):
 p=dict(saved_kwh=100,tariff=1,capex=500);p.update(kwargs)
 with pytest.raises(ValueError): investment_case(**p)

def test_no_interventions_no_cost():
 rates=dict.fromkeys(['Orientation','Shading','Glazing ratio','Insulation','Ventilation'],100)
 assert intervention_costs(Design(),Design(),Settings(),rates)==[]
