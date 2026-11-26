# Builds site/data/markets.json (UK only so far) and adds `lo` flags to site/data/countries.json.
# Usage: python3 -I scripts/build_markets.py scripts/justwatch_offers_uk.json site source/Holiday-Films-US-Ratings.csv source/Holiday-Films-by-Country-of-Origin.csv
# TODO (see CLAUDE.md section 3): generalise from the United Kingdom to every country.
import csv,json,sys,re
OFFERS,P,C1,C2=sys.argv[1:5]
jw=json.load(open(OFFERS))
g1=[r for r in csv.DictReader(open(C1,encoding='utf-8-sig')) if r['audience_market']=='United Kingdom']
g2=list(csv.DictReader(open(C2,encoding='utf-8-sig')))
by_title={}
for r in g2: by_title.setdefault(r['title'],r)
slug=lambda url: url.rstrip('/').split('/')[-1]
SUF=[' Amazon Channel',' Roku Premium Channel',' Apple TV channel',' Standard with Ads',' with Ads',' Premium Plus',' Premium',' Essential']
MAP={'Amazon Prime Video':'Prime Video','Disney Plus':'Disney+','Paramount Plus':'Paramount+','MGM Plus':'MGM+','Tubi TV':'Tubi','YouTube Free':'YouTube','Amazon Video':'Amazon','Apple TV Store':'Apple TV','Spectrum On Demand':'Spectrum','Sling Freestream Live':'Sling Freestream','Fandango At Home':'Fandango at Home','Cinepolis Cinemas':'Cinépolis'}
SKIP={'Plex Live TV'}
def brand(n):
  for s in SUF:
    if n.endswith(s): n=n[:-len(s)]
  return MAP.get(n,n)
GENERIC={'https://www.justwatch.com','https://tv.apple.com'}
def offer(offers,name,fns):
  for o in offers:
    if o['name']==name and o['fn'] in fns: return o
def group(offers,names,fns,jwurl):
  out={}
  for n in [x.strip() for x in names.split(';') if x.strip()]:
    if n in SKIP: continue
    b=brand(n); o=offer(offers,n,fns)
    url=o['url'] if o and o['url'] not in GENERIC else None
    chan='Channel' in n or 'channel' in n
    cur=out.get(b)
    if cur is None or (cur['chan'] and not chan and url): out[b]={'name':b,'url':url,'chan':chan,'price':o['price'] if o else None}
  return [{'name':v['name'],'url':v['url'],'price':v['price']} for v in out.values()]
def rentbuy(offers,rent,buy):
  r={x['name']:x for x in group(offers,rent,{'LeaseOut'},None)}
  b={x['name']:x for x in group(offers,buy,{'Sell'},None)}
  out=[]
  for n in list(r)+[k for k in b if k not in r]:
    x=r.get(n) or b.get(n)
    out.append({'name':n,'url':(r.get(n) or {}).get('url') or (b.get(n) or {}).get('url'),'rent':(r.get(n) or {}).get('price'),'buy':(b.get(n) or {}).get('price')})
  return out
def watch(row2,jwurl,fallback_sub=None):
  offers=jw[slug(jwurl)]['offers']
  if row2:
    return {'stream':group(offers,row2['subscription_services'],{'ProvideService'},jwurl),'free':group(offers,row2['free_services'],{'ProvideService'},jwurl),'rentbuy':rentbuy(offers,row2['rental_services'],row2['purchase_services'])}
  names_r=';'.join(sorted({o['name'] for o in offers if o['fn']=='LeaseOut'})); names_b=';'.join(sorted({o['name'] for o in offers if o['fn']=='Sell'}))
  return {'stream':group(offers,fallback_sub,{'ProvideService'},jwurl),'free':[],'rentbuy':rentbuy(offers,names_r,names_b)}
def poster(u): return 'posters/'+u.rstrip('/').split('/')[-1]
# --- US-made mode: UK most-watched (guide 1), US among producing countries
usmode=[]
for r in g1:
  t=r['original_title_and_english_title']; r2=by_title.get(t)
  if r2: origin=[x.strip() for x in r2['country_of_origin'].split(';')]; osrc='doc'
  else: origin=[jw[slug(r['us_watch_url'])]['origin']]; osrc='justwatch'
  if 'United States' not in origin: continue
  sub=r['us_watch_options'].rstrip('.').replace('Disney+','Disney Plus').replace('Prime Video','Amazon Prime Video')
  usmode.append({'pos':int(r['rank']),'title':t,'year':int(r['release_year']),'min':int(r['runtime_minutes']),'rating':r['us_rating_filter'] if r['us_rating_filter'] not in ('TV rating only',) else r['us_tv_rating'],'usr':r['us_mpa_rating'] or r['us_tv_rating'],'cert':r['rating_certificate'],'index':float(r['index']),'origin':origin,'originSrc':osrc,'poster':poster(r['poster_or_image_url']),'jw':r['us_watch_url'],'watch':{'US':watch(r2,r['us_watch_url'],sub)}})
# --- Country-specific mode: films made in the UK (guide 2)
local=[]
for r in g2:
  if r['country']!='United Kingdom': continue
  local.append({'pos':int(r['catalogue_position']),'title':r['title'],'year':int(r['year']),'min':int(r['runtime_minutes']),'rating':r['country_rating'] if r['rating_status'].startswith('Verified') else 'Unverified','authority':'BBFC','usr':r['us_mpa_rating'] or r['us_tv_rating'] or '','origin':[x.strip() for x in r['country_of_origin'].split(';')],'originSrc':'doc','ratingSrc':r['rating_source'],'poster':poster(r['poster_or_image_url']),'jw':r['us_watch_url'],'watch':{'US':watch(r,r['us_watch_url'])}})
markets={'GB':{'name':'United Kingdom','code':'UK','lat':54.2,'lng':-2.6,
  'us':{'sources':'National + Netflix + JustWatch index','films':usmode},
  'local':{'authority':'BBFC','scale':['U','PG','12A','15','18'],'films':local}}}
json.dump(markets,open(P+'/data/markets.json','w'),ensure_ascii=False,separators=(',',':'))
for k in ('us','local'):
  print(k)
  for f in markets['GB'][k]['films']: print('  ',f['pos'],f['title'],f['rating'],f['usr'],f['origin'],{t:[(x['name'],bool(x['url'])) for x in v] for t,v in f['watch']['US'].items()})
# --- globe flags for local mode
geo=json.load(open(P+'/data/countries.json'))
lo=set(r['country'] for r in g2)
alias={'Czechia':['Czechia','Czech Republic'],'United States':['United States of America','United States'],'South Korea':['South Korea','Korea']}
for f in geo['features']:
  p=f['properties']; nm={p['n'],p.get('m')}
  hit=next((c for c in lo if c in nm or any(a in nm for a in alias.get(c,[]))),None)
  p['lo']=('live' if hit=='United Kingdom' else 'soon' if hit else 'none')
json.dump(geo,open(P+'/data/countries.json','w'),separators=(',',':'))
print('local-mode countries on map:',sum(1 for f in geo['features'] if f['properties']['lo']!='none'),'of',len(lo))
print('unmapped:',[c for c in lo if not any(c in {f['properties']['n'],f['properties'].get('m')} or any(a in {f['properties']['n']} for a in alias.get(c,[])) for f in geo['features'])])
