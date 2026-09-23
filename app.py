"""PassiveROI — run with `streamlit run app.py`. Offline after setup."""
from dataclasses import asdict
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.config import CITIES, BUILDINGS, INSULATION, SHADING, ORIENTATIONS, YEAR
from src.climate import load_climate, provenance
from src.energy_model import Design, Settings, compare
from src.financial_model import investment_case, intervention_costs

st.set_page_config(page_title='PassiveROI · Design a better investment',page_icon='◒',layout='wide')
st.markdown('''<style>
.block-container {max-width:1450px;padding-top:2.2rem;padding-bottom:2rem}
h1 {font-size:3.1rem!important;letter-spacing:-.065em!important;font-weight:600!important;line-height:1.05!important}
h2,h3 {letter-spacing:-.035em!important} p, label {line-height:1.5}
[data-testid="stSidebar"] {border-right:1px solid #d9e1d7}
[data-testid="stMetric"] {background:#fff;border:1px solid #dce4d9;padding:19px 22px;border-radius:12px;min-height:133px}
[data-testid="stMetricValue"] {font-size:2rem;letter-spacing:-.045em}
.brand {font-size:21px;font-weight:700;letter-spacing:-1px;color:#176b57}
.eyebrow {font-size:11px;letter-spacing:2px;font-weight:650;color:#547267;text-transform:uppercase;margin:24px 0 12px}
.hero-sub {font-size:17px;color:#62736a;max-width:650px;margin:14px 0 22px}
.tag {display:inline-block;padding:6px 11px;background:#e7eee4;border:1px solid #d4dfcf;border-radius:30px;font-size:11px;letter-spacing:.7px;color:#476346;margin-right:6px}
.insight {background:#193f32;color:#edf5e8;padding:21px 25px;border-radius:12px;margin:12px 0 22px;font-size:16px}
.foot {font-size:12px;color:#738175;border-top:1px solid #d9e1d7;padding-top:18px;margin-top:25px}
[data-testid="stTabs"] button {font-size:14px}
</style>''',unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand">◒ PassiveROI</div>',unsafe_allow_html=True)
    st.caption('PASSIVE DESIGN · ACTIVE RETURNS')
    st.divider()
    st.markdown('#### 01 / Your building')
    city=st.selectbox('Location',list(CITIES),key='city')
    building=st.selectbox('Building type',list(BUILDINGS),key='building')
    c=CITIES[city];b=BUILDINGS[building];currency=c['currency']
    area=st.number_input('Conditioned floor area · m²',min_value=50.,max_value=100000.,value=b['area'],step=50.,key=f'area_{building}')
    st.caption('Concept-stage design comparison. Square footprint, equal floor plates.')
    st.markdown('#### 02 / Passive interventions')
    turn=st.checkbox('Reorient dominant glazing',value=True,key='turn')
    new_orientation=st.selectbox('Proposed glazing direction',list(ORIENTATIONS),index=0,disabled=not turn,key='new_orientation')
    shade=st.checkbox('Add external shading',value=True,key='shade')
    shade_level=st.select_slider('Shading depth',options=['Moderate','Deep'],value='Deep',disabled=not shade,key='shade_level')
    glass=st.checkbox('Reduce glazing ratio',value=False,key='glass')
    new_wwr=st.slider('Proposed window-to-wall ratio',5,90,25,5,format='%d%%',disabled=not glass,key='new_wwr')
    insulate=st.checkbox('Improve wall & roof insulation',value=False,key='insulate')
    tier=st.selectbox('Proposed insulation',list(INSULATION)[1:],disabled=not insulate,key='tier')
    with st.expander('Experimental ventilation credit'):
        st.caption('Sensible air-load scenario only. No humidity, comfort or air-quality assessment; unsuitable for design recommendations.')
        vent=st.slider('Sensible air-exchange credit',0,20,0,5,format='%d%%',key='vent')
    st.divider()
    st.caption('SCREENING ESTIMATE\n\nNot an engineering simulation or a whole-building electricity forecast.')

st.markdown('<span class="tag">DESIGN → ENERGY → VALUE</span><span class="tag">v0.1 / ESTIMATE</span>',unsafe_allow_html=True)
st.markdown('<div class="eyebrow">A better building starts with a better question.</div>',unsafe_allow_html=True)
st.title('What is passive design worth?')
st.markdown('<div class="hero-sub">Turn climate and early design choices into a transparent investment case. Compare cooling electricity, annual savings and the cost of change.</div>',unsafe_allow_html=True)

with st.expander('Baseline & operating assumptions',expanded=False):
    a1,a2,a3=st.columns(3)
    with a1:
        base_wwr=st.slider('Baseline window-to-wall ratio',5,90,int(b['wwr']*100),5,format='%d%%',key=f'base_wwr_{building}')/100
        base_orientation=st.selectbox('Baseline dominant glazing',list(ORIENTATIONS),index=3,key='base_orientation')
        base_insulation=st.selectbox('Baseline insulation',list(INSULATION),key='base_insulation')
        base_shading=st.selectbox('Baseline shading',list(SHADING),key='base_shading')
    with a2:
        floors=st.number_input('Floors',1,40,b['floors'],key=f'floors_{building}')
        height=st.number_input('Floor-to-floor height · m',2.,6.,b['height'],.1,key=f'height_{building}')
        cop=st.number_input('Cooling system COP',1.,8.,3.,.1,key='cop')
        base_temp=st.number_input('Cooling balance temperature · °C',10.,30.,18.,.5,key='base_temp')
    with a3:
        shgc=st.slider('Glazing solar heat gain coefficient',.1,.9,.6,.05,key='shgc')
        window_u=st.number_input('Window U-value · W/m²K',.5,6.,2.8,.1,key='window_u')
        share=st.slider('Glazing on dominant facade',25,100,70,5,format='%d%%',key='share')/100
        ach=st.number_input('Air changes per hour',0.,3.,.5,.1,key='ach')
    internal=st.number_input('Sensible internal gains · W/m²',0.,50.,b['internal_w'],1.,key=f'internal_{building}')
    hours=st.number_input('Internal gains · hours/day',0.,24.,b['hours'],1.,key=f'hours_{building}')
    st.caption('18°C is a screening balance temperature, not a thermostat setting. Internal gains are added explicitly; balance temperature uncertainty can materially affect absolute loads.')

settings=Settings(area,floors,height,base_temp,cop,ach,internal,hours)
baseline=Design(base_wwr,base_orientation,base_shading,base_insulation,window_u,shgc,share)
proposed=Design(new_wwr/100 if glass else base_wwr,new_orientation if turn else base_orientation,shade_level if shade else base_shading,tier if insulate else base_insulation,window_u,shgc,share,vent/100)
try:
    climate=load_climate(city);meta=provenance(city)
    result=compare(climate,baseline,proposed,settings)
except (ValueError,FileNotFoundError,KeyError) as e:
    st.error(str(e));st.stop()

for label, design, output in [('Baseline',baseline,result['baseline']),('Proposed',proposed,result['proposed'])]:
    if output['effective_dominant_share'] < design.dominant_share:
        st.caption(f"{label}: dominant-facade glazing allocation capped at {output['effective_dominant_share']:.1%} to fit the square building geometry.")

# Financial controls are declared before all summaries so every rerun is consistent.
with st.expander('Investment assumptions & editable costs',expanded=False):
    f1,f2,f3=st.columns(3)
    tariff=f1.number_input(f'Avoided electricity rate · {currency}/kWh',0.,100.,c['tariff'],.01,key=f'tariff_{city}')
    years=f2.slider('Investment horizon · years',1,30,10,key='years')
    rate=f3.slider('Discount rate',0,30,8,format='%d%%',key='discount')/100
    st.caption(c['tariff_note'])
    st.markdown(f'[Published tariff reference]({c["tariff_source"]}) · Checked 22 September 2026. Set the avoided marginal rate from your own bill; no automatic slab calculation.')
    cost_mode=st.radio('Cost basis',['Illustrative unit costs','My total project quote'],horizontal=True,key='cost_mode')
    st.caption('Illustrative costs are author-defined demo budgets, not sourced local market quotations. They must be replaced before an investment decision. Cairo has separate EGP demo amounts, not an exchange-rate conversion.')
    defaults=([5.,150.,200.,80.,10.] if currency=='AED' else [60.,1800.,2400.,960.,120.])
    names=['Orientation','Shading','Glazing ratio','Insulation','Ventilation']
    cols=st.columns(5);rates={}
    for col,name,default in zip(cols,names,defaults):
        rates[name]=col.number_input(f'{name} · {currency}/m²',0.,100000.,default,10.,key=f'cost_{name}_{city}',disabled=cost_mode!='Illustrative unit costs')
    rows=intervention_costs(baseline,proposed,settings,rates)
    suggested=sum(row['CAPEX'] for row in rows)
    quote=st.number_input(f'Total incremental project quote · {currency}',0.,1e9,0.,1000.,key=f'quote_{city}',disabled=cost_mode!='My total project quote')
    capex=suggested if cost_mode=='Illustrative unit costs' else quote
    maintenance=st.number_input(f'Incremental maintenance · {currency}/year',0.,1e7,0.,100.,key=f'maintenance_{city}')
    if rows: st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
    else: st.caption('No design changes selected; no intervention costs applied.')
    st.caption('Orientation: conditioned floor area. Shading: proposed glass area. Glazing: changed glass area. Insulation: proposed opaque wall + roof area. Ventilation: floor area. Costs represent incremental design/construction scope; use a quote for net savings from reduced glazing.')
financial=investment_case(result['saved_kwh'],tariff,capex,years,rate,maintenance)
r=result; fin=financial
st.caption(f'{city.upper()}  /  {building.upper()}  /  {area:,.0f} m²  ·  NASA POWER {YEAR}  ·  {r["baseline"]["cdd"]:,.0f} cooling degree days')
m1,m2,m3,m4=st.columns(4)
m1.metric('Estimated cooling reduction',f'{r["reduction_pct"]:.1f}%',f'{r["saved_kwh"]:,.0f} kWh / year',delta_color='normal')
m2.metric('Estimated annual bill savings',f'{currency} {fin["annual_savings"]:,.0f}',help='Cooling electricity saved × avoided electricity rate. Before incremental maintenance.')
payback=fin['payback_years']
m3.metric('Simple payback','No payback' if payback is None else f'{payback:.1f} years',help='CAPEX / annual savings net of incremental maintenance; no discounting.')
m4.metric(f'{years}-year estimated NPV',f'{currency} {fin["npv"]:,.0f}',help='CAPEX today plus discounted end-of-year net savings.')
if cost_mode=='My total project quote' and quote==0 and rows:
    st.warning('Your project quote is zero. Enter the full incremental cost before interpreting payback or NPV.')
if glass and proposed.wwr>baseline.wwr:
    st.warning('The proposed glazing ratio is higher than the baseline. This scenario increases glass area.')
if payback is not None and payback>years:
    insight=f'Payback extends beyond the {years}-year investment horizon. The energy benefit does not recover the assumed cost within this period.'
elif fin['npv']>0:
    insight=f'This scenario returns an estimated {currency} {fin["npv"]:,.0f} above the initial investment in discounted net savings over {years} years.'
else:
    insight=f'This scenario has a non-positive {years}-year NPV at a {rate:.0%} discount rate. Review the intervention scope, costs and operating assumptions.'
st.markdown(f'<div class="insight">{insight}</div>',unsafe_allow_html=True)
st.caption(f'FINANCIAL BASIS: {cost_mode.upper()} · No energy-price escalation, financing, tax, residual value or equipment replacement.')

energy_tab,finance_tab,data_tab,method_tab=st.tabs(['Energy comparison','Investment case','Climate & provenance','How it works'])
COLORS=['#a6b4a3','#176b57']
def style(fig,height=330):
    fig.update_layout(template='plotly_white',height=height,margin=dict(l=12,r=12,t=25,b=20),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(family='Arial',color='#3e594b'),legend=dict(orientation='h',y=1.15,x=0),hoverlabel=dict(bgcolor='white'))
    fig.update_yaxes(gridcolor='#e1e7dd',zerolinecolor='#c5d2c0')
    return fig
with energy_tab:
    left,right=st.columns([1,1.5])
    with left:
        st.subheader('Less cooling. Same building.')
        st.caption('Estimated cooling electricity · kWh/m²/year')
        fig=go.Figure(go.Bar(x=['Baseline','Proposed'],y=[r['baseline']['kwh_per_sqm'],r['proposed']['kwh_per_sqm']],marker_color=COLORS,text=[f"{r[k]['kwh_per_sqm']:.1f}" for k in ['baseline','proposed']],textposition='outside',width=.48))
        fig.update_layout(showlegend=False);fig.update_yaxes(title='kWh electricity / m² / year',rangemode='tozero')
        st.plotly_chart(style(fig),width='stretch',config={'displayModeBar':False})
    with right:
        st.subheader('Where the difference comes from')
        st.caption('Components of modelled annual cooling electricity · kWh/m²/year')
        fig=go.Figure()
        for label,key,color in zip(['Baseline','Proposed'],['baseline','proposed'],COLORS):
            comp=r[key]['components'];fig.add_trace(go.Bar(name=label,y=list(comp),x=[v/area for v in comp.values()],orientation='h',marker_color=color))
        fig.update_layout(barmode='group');st.plotly_chart(style(fig),width='stretch',config={'displayModeBar':False})
    st.subheader('A year in your climate')
    fig=go.Figure()
    for label,key,color in zip(['Baseline','Proposed'],['baseline','proposed'],COLORS):
        monthly=r[key]['monthly'];fig.add_trace(go.Scatter(x=monthly.index,y=monthly.sum(axis=1)/area,name=label,mode='lines+markers',line=dict(color=color,width=3)))
    fig.update_yaxes(title='kWh electricity / m² / month');fig.update_xaxes(tickformat='%b',dtick='M1')
    st.plotly_chart(style(fig,270),width='stretch',config={'displayModeBar':False})
with finance_tab:
    st.subheader('Does the investment pay back?')
    f1,f2,f3=st.columns(3)
    f1.metric('Incremental CAPEX',f'{currency} {capex:,.0f}')
    f2.metric('Annual net savings',f'{currency} {fin["annual_net_savings"]:,.0f}')
    f3.metric('Required return',f'{rate:.0%}')
    fig=go.Figure()
    for label,key,color in [('Undiscounted','cumulative','#a6b4a3'),('Discounted','cumulative_discounted','#176b57')]:
        fig.add_trace(go.Scatter(x=list(range(years+1)),y=fin[key],name=label,mode='lines+markers',line=dict(color=color,width=3)))
    fig.add_hline(y=0,line_dash='dot',line_color='#899987');fig.update_yaxes(title=f'Cumulative net value · {currency}');fig.update_xaxes(title='Year',dtick=1)
    st.plotly_chart(style(fig,380),width='stretch')
    st.latex(r'NPV = -CAPEX + \sum_{t=1}^{N} \frac{\Delta kWh\times tariff-maintenance}{(1+r)^t}')
    cash=pd.DataFrame({'Year':range(years+1),'Cash flow':fin['cashflows'],'Cumulative':fin['cumulative'],'Discounted cumulative':fin['cumulative_discounted']})
    st.dataframe(cash,hide_index=True,width='stretch')
with data_tab:
    st.subheader('Real weather. Traceable inputs.')
    st.caption('NASA POWER gridded historical estimates, not on-site measurements or a typical meteorological year.')
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=climate.index,y=climate.t_max,name='Daily maximum',line=dict(color='#c4a16a',width=1)))
    fig.add_trace(go.Scatter(x=climate.index,y=climate.t_mean,name='Daily mean',line=dict(color='#176b57',width=1.5)))
    fig.update_yaxes(title='Temperature · °C');st.plotly_chart(style(fig),width='stretch')
    st.caption(f"{len(climate)} days · August mean daily maximum {meta['august_mean_daily_max_c']:.1f}°C · Annual GHI {climate.ghi.sum():,.0f} kWh/m²")
    st.markdown(f'[NASA daily request]({meta["daily"]["url"]}) · [NASA hourly solar request]({meta["hourly"]["url"]})')
    st.download_button('Download climate CSV',climate.to_csv(),file_name=f'{c["slug"]}_{YEAR}_climate.csv',mime='text/csv')
    with st.expander('Dataset provenance'):st.json(meta)
with method_tab:
    st.subheader('An estimate you can interrogate')
    st.markdown('**1. Climate → heat gains.** Daily cooling degree days drive conductive and sensible air-exchange gains. NASA hourly solar data is transposed to each vertical facade using pvlib.\n\n**2. Design → electricity.** Glazing area, SHGC, shading and wall/roof U-values change the relevant components. Their sum is divided by COP.\n\n**3. Electricity → investment case.** Avoided electricity × your tariff gives annual bill savings. CAPEX and annual maintenance feed simple payback and discounted NPV.')
    st.warning('This is a sensible-cooling screening model. It omits humidity/dehumidification, thermal mass, hourly controls, daylight/lighting trade-offs, roof solar absorption, equipment part-load behaviour and microclimate. Absolute energy totals and savings are uncertain; this is not an engineering-grade prediction.')
    st.markdown('**Evidence status.** Historical weather and tariff references are sourced. Geometry, use profiles, legacy insulation, shading factors and demo costs are explicit scenario assumptions. The Zawaya comparator was supplied in the project brief and has not been independently verified. No coefficients were fitted to it.')
    method=Path(__file__).with_name('methodology.md')
    if method.exists():
        with st.expander('Full methodology & sources'):st.markdown(method.read_text())

export={'model_version':'0.1.0','status':'screening estimate','city':city,'building_type':building,'currency':currency,'climate_year':YEAR,'climate_sha256':meta['sha256'],'settings':asdict(settings),'baseline_design':asdict(baseline),'proposed_design':asdict(proposed),'baseline_kwh_per_sqm':r['baseline']['kwh_per_sqm'],'proposed_kwh_per_sqm':r['proposed']['kwh_per_sqm'],'reduction_pct':r['reduction_pct'],'tariff':tariff,'tariff_source':c['tariff_source'],'cost_basis':cost_mode,'unit_costs':rates,'cost_breakdown':rows,'annual_maintenance':maintenance,'financial':fin,'limitations':'Sensible cooling only; scenario assumptions, not engineering validation. Illustrative costs are not quotations.'}
st.download_button('↓ Export this scenario · JSON',json.dumps(export,indent=2,allow_nan=False),file_name='passiveroi-scenario.json',mime='application/json')
st.markdown('<div class="foot">PASSIVEROI  /  Climate data → design decisions → commercial value<br>Portfolio demonstration · All results are estimates · NASA POWER historical climate · Python + Streamlit</div>',unsafe_allow_html=True)
