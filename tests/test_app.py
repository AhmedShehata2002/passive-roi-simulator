from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]

def test_all_cities_and_no_intervention():
 a=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
 assert not a.exception
 for city in ['Dubai','Cairo','Abu Dhabi']:
  a.selectbox(key='city').set_value(city).run()
  assert not a.exception
  assert any(('EGP' if city=='Cairo' else 'AED') in m.value for m in a.metric)
 a.checkbox(key='turn').uncheck();a.checkbox(key='shade').uncheck();a.run()
 assert not a.exception
 assert a.metric[0].value=='0.0%'
 assert a.metric[2].value=='No payback'
 assert a.metric[3].value=='AED 0'

def test_proposed_changes_and_quote():
 a=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
 a.checkbox(key='glass').check();a.checkbox(key='insulate').check();a.run()
 assert not a.exception
 reduction=float(a.metric[0].value.rstrip('%'))
 assert reduction>15
 a.radio(key='cost_mode').set_value('My total project quote').run()
 assert any('quote is zero' in w.value for w in a.warning)
 a.number_input(key='quote_Abu Dhabi').set_value(10000.).run()
 assert not a.exception
 assert a.metric[4].value=='AED 10,000'
 a.selectbox(key='building').set_value('Villa').run()
 assert not a.exception
