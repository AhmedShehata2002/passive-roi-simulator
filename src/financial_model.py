"""Unlevered, constant annual end-of-year savings; no tax or escalation."""
from math import isfinite

def investment_case(saved_kwh,tariff,capex,years=10,discount_rate=.08,annual_maintenance=0.):
    if not all(isfinite(x) for x in [saved_kwh,tariff,capex,discount_rate,annual_maintenance,years]):
        raise ValueError('Financial inputs must be finite.')
    if tariff<0 or capex<0 or annual_maintenance<0 or not 0<=discount_rate<=1 or not 1<=years<=50 or int(years)!=years:
        raise ValueError('Invalid financial inputs.')
    annual=saved_kwh*tariff
    net=annual-annual_maintenance
    discounted=[net/(1+discount_rate)**t for t in range(1,int(years)+1)]
    cashflows=[-capex]+[net]*int(years)
    cumulative=[-capex]; cumulative_discounted=[-capex]
    for flow,disc in zip(cashflows[1:],discounted):
        cumulative.append(cumulative[-1]+flow);cumulative_discounted.append(cumulative_discounted[-1]+disc)
    return {'annual_savings':annual,'annual_net_savings':net,'capex':capex,'npv':sum(discounted)-capex,'payback_years':capex/net if net>0 else None,'cashflows':cashflows,'cumulative':cumulative,'cumulative_discounted':cumulative_discounted,'years':int(years),'discount_rate':discount_rate}

def intervention_costs(baseline,proposed,settings,rates):
    """Incremental cost by actual treatment area; rates are user assumptions.
    Orientation is a new-design fee on floor area. Glazing rate is net cost per
    m² of changed window area, not a claim that reducing glass always costs more.
    """
    from src.energy_model import geometry
    if any(not isfinite(x) or x<0 for x in rates.values()): raise ValueError('Invalid cost rate.')
    b=geometry(settings,baseline);p=geometry(settings,proposed)
    areas={
        'Orientation':settings.area if baseline.orientation!=proposed.orientation else 0.,
        'Shading':p['window'] if baseline.shading!=proposed.shading else 0.,
        'Glazing ratio':abs(b['window']-p['window']),
        'Insulation':p['wall']+p['roof'] if baseline.insulation!=proposed.insulation else 0.,
        'Ventilation':settings.area if baseline.ventilation_credit!=proposed.ventilation_credit else 0.,
    }
    return [{'Intervention':name,'Treated area (m²)':area,'Rate / m²':rates[name],'CAPEX':area*rates[name]} for name,area in areas.items() if area>0]
