"""Reproduce sample outputs and the owner-supplied comparator."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.config import CITIES,ROOT
from src.climate import load_climate
from src.energy_model import Design,Settings,compare
from src.financial_model import investment_case,intervention_costs

rows=[]
for city,c in CITIES.items():
 b=Design();p=Design(orientation='North',shading='Deep');s=Settings()
 rates=dict(zip(['Orientation','Shading','Glazing ratio','Insulation','Ventilation'],[5,150,200,80,10] if c['currency']=='AED' else [60,1800,2400,960,120]))
 cost=sum(x['CAPEX'] for x in intervention_costs(b,p,s,rates))
 r=compare(load_climate(city),b,p,s)
 f=investment_case(r['saved_kwh'],c['tariff'],cost)
 rows.append({'city':city,'currency':c['currency'],'baseline_kwh_per_sqm':r['baseline']['kwh_per_sqm'],'proposed_kwh_per_sqm':r['proposed']['kwh_per_sqm'],'reduction_pct':r['reduction_pct'],'cost_basis':'illustrative author budgets, not local quotations','financial':f})
(ROOT/'docs'/'sample-outputs.json').write_text(json.dumps(rows,indent=2,allow_nan=False))
print(json.dumps(rows,indent=2))
