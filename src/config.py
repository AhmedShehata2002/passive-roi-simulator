"""Explicit scenario inputs; provenance and limitations in methodology.md."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
YEAR = 2025
CITIES = {
 'Abu Dhabi': {'slug':'abu_dhabi','lat':24.4539,'lon':54.3773,'currency':'AED','tariff':0.20,'tariff_note':'Commercial flat energy rate, published 2025; excludes VAT. Verify your account rate.','tariff_source':'https://www.addc.ae/en-US/business/Pages/RatesAndTariffs2025.aspx'},
 'Dubai': {'slug':'dubai','lat':25.2048,'lon':55.2708,'currency':'AED','tariff':0.44,'tariff_note':'Commercial/residential top marginal slab 0.38 + September 2026 fuel surcharge 0.06; excludes VAT. Not a whole-bill calculator.','tariff_source':'https://www.dewa.gov.ae/en/consumer/billing/slab-tariff'},
 'Cairo': {'slug':'cairo','lat':30.0444,'lon':31.2357,'currency':'EGP','tariff':2.79,'tariff_note':'Commercial >1,000 kWh/month, EgyptERA April 2026 published schedule; excludes stamps/fees. Confirm current bill before use.','tariff_source':'https://egyptera.org/en/TarrifApril2026.aspx'},
}
# Author-defined geometrical/use archetypes, not measured building stock.
BUILDINGS = {
 'Low-rise commercial': {'area':2000.,'floors':2,'wwr':0.40,'height':3.5,'internal_w':12.,'hours':12.},
 'Villa': {'area':400.,'floors':2,'wwr':0.30,'height':3.0,'internal_w':5.,'hours':16.},
 'Mid-rise residential': {'area':6000.,'floors':6,'wwr':0.35,'height':3.0,'internal_w':5.,'hours':16.},
}
# W/m²K: legacy & high-performance = illustrative; improved anchored in
# Dubai Green Building Regulations 501.01 (historical reference, not compliance).
INSULATION = {'Legacy / standard': (1.5,1.2), 'Improved': (0.57,0.30), 'High-performance': (0.28,0.20)}
# Illustrative annual solar transmission factors, NOT published savings claims.
SHADING = {'None':1.0,'Moderate':0.75,'Deep':0.60}
ORIENTATIONS = {'North':0,'East':90,'South':180,'West':270}
