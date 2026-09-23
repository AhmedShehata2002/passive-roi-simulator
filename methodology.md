# PassiveROI methodology · v0.1

Build date: 22 September 2026. All results are **screening estimates** of annual sensible cooling electricity. This is not an engineering simulation, a code compliance assessment or a whole-building electricity forecast.

## Evidence hierarchy

Downloaded climate data, reference-backed physical relationships and author-defined scenario inputs are distinguished below. A source describing a relationship does **not** validate an illustrative numerical default. No generic “ASHRAE rule of thumb” citation is used to disguise unsupported coefficients.

## 1. Climate and solar exposure

NASA POWER [R1] supplies daily `T2M`, `T2M_MAX`, `ALLSKY_SFC_SW_DWN`, and hourly `ALLSKY_SFC_SW_DWN`, `ALLSKY_SFC_SW_DNI`, `ALLSKY_SFC_SW_DIFF` for 2025. This is the most recent full calendar year, not a typical meteorological year. Temperatures are °C, daily radiation kWh/m²/day, hourly radiation W/m². Returned parameter units are retained in cache metadata.

Locations: Abu Dhabi (24.4539, 54.3773), Dubai (25.2048, 55.2708), Cairo (30.0444, 31.2357). These are central-city examples, not parcel locations. Aggregation uses UTC consistently. NASA POWER is gridded satellite/reanalysis-derived information, not an on-site weather station.

The setup script requests 8,760 hourly solar records per city. pvlib calculates solar position at interval midpoints, then transposes direct, diffuse and ground-reflected radiation onto vertical north/east/south/west planes using an isotropic sky model [R2]. Ground albedo 0.20 is an **author assumption**. Hourly W/m² × one hour / 1,000 is summed to daily kWh/m². No synthetic weather or arbitrary orientation penalty table is used. This ignores anisotropic diffuse sky, neighbouring obstructions and facade reflections; midpoint geometry approximates each hour.

Caches require 365 ordered dates, finite values, no NASA sentinels, plausible temperatures and nonnegative radiation. Hourly coverage is checked before aggregation. JSON sidecars preserve source requests, timestamps, NASA metadata, pvlib version and CSV SHA-256. Updating climate is explicit; the app never downloads it. Raw hourly data is not bundled; source requests reproduce it.

## 2. Geometry and scenario assumptions

Equal square floor plates give footprint `floor_area / floors`, perimeter `4 × sqrt(footprint)`, facade `perimeter × height × floors`, windows `facade × WWR`, and opaque wall `facade × (1 − WWR)`. Roof equals footprint. Conditioned floor area includes all storeys.

| Archetype | Area m² | Floors | Height m | WWR | Internal W/m² | Hours/day |
|---|---:|---:|---:|---:|---:|---:|
| Low-rise commercial | 2,000 | 2 | 3.5 | 0.40 | 12 | 12 |
| Villa | 400 | 2 | 3.0 | 0.30 | 5 | 16 |
| Mid-rise residential | 6,000 | 6 | 3.0 | 0.35 | 5 | 16 |

These are **author-defined demonstration archetypes**, not published building-stock averages. All are editable. Initially 70% of glazing faces west and 10% each faces north/east/south. Orientation rotates this distribution, not the entire energy total. Equal 25% distribution eliminates the orientation effect. This abstraction is intended for concept-stage design, not physical rotation of existing buildings. The dominant glazing share is capped at `1 / (4 × WWR)` to fit within one facade of the square footprint. The remaining glass is divided across the other three sides. Any cap is shown in the UI. Detailed facade layout and obstruction modelling are still omitted.

## 3. Cooling equations and coefficients

For day d, thermal loads Q are kWh; electrical energy E is kWh:

```
CDD_d = max(T_mean,d − T_base, 0)
CoolingDay_d = 1 if T_mean,d > T_base, otherwise 0
UA = U_wall × A_opaque + U_roof × A_roof + U_window × A_window
Q_envelope,d = UA × 24 × CDD_d / 1000
I_glazing,d = sum(facade radiation_d × glazing distribution share)
Q_solar,d = A_window × SHGC × shading_factor × I_glazing,d × CoolingDay_d
Q_air,d = 0.335 × ACH × floor_area × height × 24 × CDD_d / 1000 × (1 − credit)
Q_internal,d = internal_W_m2 × hours_per_day × floor_area / 1000 × CoolingDay_d
E_electric,d = (Q_envelope,d + Q_solar,d + Q_air,d + Q_internal,d) / COP
Annual intensity = sum(E_electric,d) / floor_area
```

Conduction uses the UA principle [R3]. SHGC represents admitted solar gain [R4]. The 0.335 Wh/(m³ K) constant comes from approximate dry-air density 1.2 kg/m³ × specific heat 1,005 J/(kg K) / 3,600. The factors 24 and 1,000 convert days to hours and W to kW; they are not fitted coefficients.

| Input | Default / tiers | Evidence status |
|---|---|---|
| Cooling base | 18°C | Brief-requested screening convention; caveat below |
| COP | 3.0 | Brief-requested constant scenario, not measured seasonal efficiency |
| ACH | 0.50 | Author assumption, not code ventilation sizing |
| Window U-value | 2.8 W/m²K | Illustrative glazing, editable |
| Window SHGC | 0.60 | Illustrative glazing, editable |
| Legacy wall / roof U | 1.5 / 1.2 W/m²K | Author legacy-envelope example, not a current-code baseline |
| Improved wall / roof U | 0.57 / 0.30 W/m²K | Historical Dubai Green Building Regulations §501.01 [R5]; not certification of current compliance |
| High-performance wall / roof U | 0.28 / 0.20 W/m²K | Author performance targets, not certified assemblies |
| Solar transmission under shading | None 1.0; moderate 0.75; deep 0.60 | Author annual scenarios; no claim of universal overhang performance |
| Ventilation credit | Default 0%; range 0–20% | Hypothetical reduction of sensible air-exchange load only |

**Balance-temperature caveat:** 18°C is retained from the brief, not a GCC-calibrated thermostat or balance point. Adding explicit internal/solar gains to a low balance-temperature approach risks double-counting gains a calibrated balance point already represents. Absolute intensities should not be used as utility forecasts. The editable base allows inspection of this structural uncertainty. An hourly setpoint-based heat balance is future work. Daily means miss hot hours on mild days and thermal storage.

Shading changes solar gains only. Insulation changes envelope conduction only. Glazing changes solar gains, window conduction and opaque-wall area together. Savings percentages are not added across interventions. “Moderate” and “deep” do not calculate actual overhang geometry; angle, fins, reveals and diffuse light require a more detailed model.

Ventilation does not calculate enthalpy, humidity, wind, opening schedules or indoor air quality. The optional credit cannot justify reducing required fresh air or establish that natural ventilation is suitable. Default zero reflects the evidence gap. No coefficients are calibrated to the Zawaya claim.

## 4. Tariffs and local currency

Reviewed 22 September 2026. Outputs stay in city currency; there is no USD or silent FX conversion.

| City | Default | Meaning |
|---|---|---|
| Abu Dhabi | 0.20 AED/kWh | Commercial energy rate on the 2025 business tariff page [R6], excluding VAT; verify current applicability. |
| Dubai | 0.44 AED/kWh | Top residential/commercial marginal slab 0.38 + September 2026 surcharge 0.06 [R7], excluding VAT. |
| Cairo | 2.79 EGP/kWh | Commercial >1,000 kWh/month rate on EgyptERA's April 2026 published schedule [R8], excluding stamps and fees. Verify current bill. |

These are **commercial-scenario defaults**, even for residential archetypes. Change the tariff for the actual account. Slab crossings and tariff thresholds are not modelled; avoided marginal rate × kWh is a simplification. Fixed meter charges are not avoided. Cairo's retrieved official page remains labelled April 2026; subsequent changes are not assumed resolved. Customer-specific subsidies and tax are excluded.

## 5. CAPEX evidence gap

Current local installation-cost ranges could **not be verified** during this build. NREL's public resources [R9] provide further cost-research leads, but direct report retrieval failed and US retrofit data is not a local quotation. The brief's sourced local CAPEX requirement remains open.

The app explicitly offers **illustrative unit costs** and **my total project quote**. Quote mode starts at zero with a warning if interventions are selected. Replace demo budgets before investment decisions.

| Intervention | Quantity basis | Illustrative AED/m² | Illustrative EGP/m² |
|---|---|---:|---:|
| Orientation redesign | Conditioned floor area | 5 | 60 |
| Shading | Proposed window area | 150 | 1,800 |
| Glazing-ratio change | Absolute changed window area | 200 | 2,400 |
| Insulation | Proposed opaque wall + roof | 80 | 960 |
| Ventilation provisions | Conditioned floor area | 10 | 120 |

These values are **author demo budgets**, not market-price claims or sourced ranges. EGP amounts are separate examples, not currency conversions. Only changed categories incur costs. Tier downgrades still use the editable category rate. Reduced glazing may save construction costs; use a net incremental quote instead. Negative CAPEX is not supported. Costing omits permits, disruption, financing, detailed bills of quantities and replacement cycles.

## 6. Financial model

```
Annual bill savings = (baseline kWh − proposed kWh) × avoided tariff
Net annual savings = bill savings − incremental maintenance
Simple payback = CAPEX / net annual savings, only if net savings > 0
NPV = −CAPEX + sum(net annual savings / (1 + r)^t, t = 1 … N)
```

CAPEX occurs at year zero, equal savings at each year end. Defaults: 10 years, 8% discount rate (brief assumptions). Unlevered, pre-tax, constant-price calculation with no escalation, depreciation, financing, residual value or renewal CAPEX. Cash-flow and discount-rate assumptions need consistent real/nominal treatment. Zero/negative savings gives “No payback”; free beneficial changes have zero payback. Payback beyond the horizon remains visible; NPV remains signed.

Hand check: CAPEX 1,000, annual savings 1,000, 10%, two years → NPV `−1000 + 1000/1.1 + 1000/1.1² = 735.54`; payback one year.

## 7. Zawaya plausibility comparison

The brief supplies 625.5 → 363.2 kWh/m²/year, a 41.9345% reduction. An independently accessible original publication was not located. It is an **owner-supplied comparator**, not independently verified evidence.

The notebook uses Cairo, the commercial archetype, west-dominant glazing and legacy insulation; changes only north orientation, deep shading and 10% hypothetical sensible ventilation credit. Model result: **22.13%** versus supplied **41.93%**, a gap of **19.80 percentage points**. This checks direction and rough scale, not accuracy. No tuning closes the gap. The broad positive/below-100% test is only a regression sanity check.

The case says cooling demand (possibly thermal), while dashboard values are cooling electricity after COP. Both quantities are shown in the notebook, but unlike absolute intensities are not equated. Original weather, geometry, schedules and simulation settings are unavailable. Field data and a separately parameterised EnergyPlus comparison are needed for validation.

## 8. Limits and proper use

Omitted: latent/dehumidification cooling, thermal mass and transient heat transfer, thermal bridges, pressure-driven infiltration, HVAC part-load performance, roof solar absorption, ground conduction, daylight/lighting feedback, occupant behaviour variation, construction quality and local microclimate. Internal gains count only on days above the cooling base. This is neither a total electric bill nor an annual dynamic building simulation. No statistical confidence interval is claimed; one historical year does not describe future weather uncertainty.

Use this portfolio demonstration to frame early design and commercial questions. Detailed simulation and project-specific quotations remain necessary before investment or construction decisions.

## References

- **R1 — NASA POWER:** [Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/), [Hourly API](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/), [Parameters](https://power.larc.nasa.gov/docs/tutorials/parameters/). Exact requests/units are in cache sidecars.
- **R2 — pvlib:** [Total in-plane irradiance](https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.irradiance.get_total_irradiance.html), [Solar position](https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.solarposition.get_solarposition.html). These support solar transposition, not accuracy of the building model.
- **R3 — DOE:** [Single Family v2 training](https://www.energy.gov/cmei/buildings/doe-efficient-new-homes-single-family-version-2-rev-3-web-transcript), UA principle, not scenario coefficients.
- **R4 — DOE:** [Window technologies](https://www.energy.gov/energysaver/window-types-and-technologies), [Efficient window purchasing](https://www.energy.gov/cmei/femp/purchasing-energy-efficient-residential-windows-doors-and-skylights). U-factor and SHGC principles.
- **R5 — Dubai:** [Historical Green Building Regulations](https://beta.government.ae/-/media/Documents-2023/05_ENG_DCL_LawsLegislation_EngineeringSection_GreenBuildingRegulation-%281%29.pdf), §501.01; [Municipality code portal](https://www.dm.gov.ae/municipality-business/planning-and-construction/dubai-building-code-2/). No assertion of present code compliance.
- **R6 — ADDC/TAQA:** [Business tariffs 2025](https://www.addc.ae/en-US/business/Pages/RatesAndTariffs2025.aspx). Official search extract retrieved; full page failed to load.
- **R7 — DEWA:** [Slab tariff](https://www.dewa.gov.ae/en/consumer/billing/slab-tariff), September 2026 surcharge shown in retrieved page.
- **R8 — EgyptERA:** [April 2026 tariff](https://egyptera.org/en/TarrifApril2026.aspx). 279 piastres/kWh = 2.79 EGP/kWh.
- **R9 — Further cost research only:** [NREL REMDB](https://data.openei.org/submissions/8336), [NREL window report landing page](https://research-hub.nlr.gov/en/publications/measure-guideline-energy-efficient-window-performance-and-selecti/). No numerical local cost support established.
