# Builds data/countries.json from Natural Earth 1:50m (raw.githubusercontent.com is reachable).
# Source: https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson
# Usage: python3 -I prep_countries.py ne50.geojson Holiday-Films-US-Ratings.csv out/countries.json
# Feature properties written: n (NAME), m (matched audience_market or null), iso (ISO_A2_EH, else ISO_A2),
#   lx/ly (LABEL_X/LABEL_Y, used for fly-to), st (US-movies mode status: live|soon|none).
# build_markets.py later adds lo (Country-specific mode status) using the origin CSV's `country` column.
import json,sys,csv
g=json.load(open(sys.argv[1]))
mk=set(r['audience_market'] for r in csv.DictReader(open(sys.argv[2],encoding='utf-8-sig')))
def rnd(c):
  if isinstance(c[0],(int,float)): return [round(c[0],3),round(c[1],3)]
  return [rnd(x) for x in c]
out=[]
for f in g['features']:
  p=f['properties']
  keys={p.get(k) for k in ('NAME','NAME_LONG','ADMIN','NAME_EN','FORMAL_EN')}
  m=next((k for k in keys if k in mk),None)
  iso=p['ISO_A2_EH'] if p.get('ISO_A2_EH') not in (None,'-99') else p.get('ISO_A2')
  st='live' if m=='United Kingdom' else ('soon' if m else 'none')
  out.append({'type':'Feature','properties':{'n':p['NAME'],'m':m,'iso':iso,'lx':round(p['LABEL_X'],2),'ly':round(p['LABEL_Y'],2),'st':st},'geometry':{'type':f['geometry']['type'],'coordinates':rnd(f['geometry']['coordinates'])}})
json.dump({'type':'FeatureCollection','features':out},open(sys.argv[3],'w'),separators=(',',':'))
