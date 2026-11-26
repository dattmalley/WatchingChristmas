# Builds site/data/markets.json for every country with data and sets the per-mode globe status in site/data/countries.json.
# Usage:
#   python3 -I scripts/build_markets.py scripts/justwatch_offers.json site source/Holiday-Films-US-Ratings.csv source/Holiday-Films-by-Country-of-Origin.csv [source/Holiday-Film-Trailers.csv]
# Also writes scripts/posters_manifest.json (poster file -> source image URL) for scripts/fetch_posters.py.
# Run order: fetch_justwatch_offers.py -> build_markets.py -> fetch_posters.py -> build_markets.py (picks up the downloaded posters).
#
# Decisions (agreed with Matt, Nov 2026):
#   - Global Top 10 mode (data key 'us') = guide 1 most-watched list per audience_market, all films (the US-made filter was removed 26 Nov 2026).
#   - Country specific = guide 2 films made in that country, rated by that country's own board. Never convert ratings.
#   - "Global Top Ten" -> its own market (key GLOBAL), opened from a button.  "China unranked example" -> dropped.
#   - Guadeloupe, Martinique, Reunion -> own markets (GP, MQ, RE), shown as map markers.
#   - "Soviet Union" (guide 2) -> merged into Russia's Country specific list, each film labelled.
#   - Origin: guide 2 by title (normalised) + year, or by watch URL; else JustWatch countryOfOrigin, flagged.
import csv,json,sys,re,os,unicodedata,collections
OFFERS,P,C1,C2=sys.argv[1:5]
C3=sys.argv[5] if len(sys.argv)>5 else None   # optional trailers CSV: one row per film or per country entry, with trailer_url
HERE=os.path.dirname(os.path.abspath(__file__))
jw=json.load(open(OFFERS))
g1=list(csv.DictReader(open(C1,encoding='utf-8-sig')))
g2=list(csv.DictReader(open(C2,encoding='utf-8-sig')))
# JustWatch pages found by title + matching year for guide-2 films whose own link is missing, dead or not on JustWatch
# (scripts/find_justwatch_slugs.py); the guide's link is kept as orig_url for direct service links.
_mp=os.path.join(HERE,'justwatch_slug_matches.json')
SLUG_MATCH=json.load(open(_mp)) if os.path.exists(_mp) else {}
for r in g2:
  hit=SLUG_MATCH.get(f"{r['title']}|{r['year']}")
  if hit and hit in jw: r['orig_url']=r['us_watch_url']; r['us_watch_url']='https://www.justwatch.com/us/movie/'+hit
geo=json.load(open(P+'/data/countries.json'))
JWP='https://www.justwatch.com/us/movie/'

# ---------- names -> ISO2 ----------
ISO={}
for f in geo['features']:
  p=f['properties']
  for k in (p['n'],p.get('m')):
    if k and p['iso'] not in (None,'-99'): ISO.setdefault(k,p['iso'])
ISO.update({'Czech Republic':'CZ','Czechia':'CZ','Soviet Union':'RU','Global Top Ten':'GLOBAL','Guadeloupe':'GP','Martinique':'MQ','Réunion':'RE'})
SKIP_MARKETS={'China unranked example'}
FEAT={f['properties']['iso']:f['properties'] for f in geo['features']}
EXTRA_POS={'GP':(16.25,-61.58),'MQ':(14.64,-61.02),'RE':(-21.12,55.53),'GLOBAL':(20,0)}
SHORT={'United Kingdom':'UK','United States':'US','United Arab Emirates':'UAE','Global Top Ten':'global','Czech Republic':'Czech Republic'}
THE={'United Kingdom','United States','United Arab Emirates','Netherlands','Philippines','Czech Republic','Dominican Republic','Bahamas','Maldives','Global Top Ten'}
DISPLAY={'Czech Republic':'Czechia'}   # one name per shape; guide 1 says Czech Republic, guide 2 Czechia

def norm(t):
  t=unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode().lower().replace('&','and')
  return ' '.join(re.sub(r'[^a-z0-9 ]',' ',t).split())
# guide watch URLs that are not JustWatch pages but have one (verified: same Netflix title ID in the JustWatch watch link)
SLUG_ALIAS={'https://www.netflix.com/title/82090597':'a-dogs-perfect-christmas',
            # guide link is dead; this page is the 1947 film (dateCreated 1947, made in the US)
            'https://www.justwatch.com/us/movie/miracle-on-34th-street-1947':'miracle-on-34th-street',
            # guide 1 gives the 1994 film the 1947 film's page; the 1994 film has its own (dateCreated 1994)
            'https://www.justwatch.com/us/movie/miracle-on-34th-street':'miracle-on-34th-street-1994'}
def slug(url): return SLUG_ALIAS.get(url) or (url.rstrip('/').split('/')[-1] if url.startswith(JWP) else None)
def jwrec(url): return jw.get(slug(url) or '',None)
import urllib.parse
def jwlink(url,title):
  # the JustWatch page when it exists; otherwise (dead page or a non-JustWatch source) a JustWatch search for the title
  return JWP+slug(url) if jwrec(url) else 'https://www.justwatch.com/us/search?q='+urllib.parse.quote(re.sub(r'\s*\(.*?\)\s*$','',title))

# ---------- watch options (rules: Stream > Free > Rent/Buy, max 3 in the UI, no prices shown) ----------
SUF=[' Amazon Channel',' Roku Premium Channel',' Apple TV channel',' Apple TV Channel',' Standard with Ads',' with Ads',' Premium Plus',' Premium',' Essential']
MAP={'Amazon Prime Video':'Prime Video','Disney Plus':'Disney+','Paramount Plus':'Paramount+','MGM Plus':'MGM+','Tubi TV':'Tubi','YouTube Free':'YouTube','Amazon Video':'Amazon','Apple TV Store':'Apple TV','Spectrum On Demand':'Spectrum','Sling Freestream Live':'Sling Freestream','Fandango At Home':'Fandango at Home','Cinepolis Cinemas':'Cinépolis','fuboTV':'Fubo','Fubo TV':'Fubo'}
SKIP={'Plex Live TV'}
GENERIC={'https://www.justwatch.com','https://tv.apple.com'}
def brand(n):
  n=n.strip()
  for s in SUF:
    if n.endswith(s): n=n[:-len(s)]
  return MAP.get(n,n)
bkey=lambda n: re.sub(r'[^a-z0-9]','',brand(n).lower())
# a non-JustWatch watch URL on the service's own site is itself a direct link
DOMAIN={'netflix.com':'Netflix','tubitv.com':'Tubi','primevideo.com':'Prime Video','tv.apple.com':'Apple TV','youtube.com':'YouTube','roku.com':'The Roku Channel'}
def own_link(url,b):
  for d,name in DOMAIN.items():
    if d in (url or '') and bkey(name)==bkey(b): return url
def offer(offers,name,fns):
  for o in offers:
    if o['name']==name and o['fn'] in fns: return o
  for o in offers:
    if bkey(o['name'])==bkey(name) and o['fn'] in fns: return o
def split_names(s): return [x.strip() for x in re.split(r'[;,]',s or '') if x.strip()]
def group(offers,names,fns,wurl):
  out={}
  for n in names:
    if n in SKIP: continue
    b=brand(n); o=offer(offers,n,fns)
    url=o['url'] if o and o['url'] not in GENERIC else own_link(wurl,b)
    chan='channel' in n.lower()
    cur=out.get(b)
    if cur is None or (cur['chan'] and not chan and url): out[b]={'name':b,'url':url,'chan':chan}
  return [{'name':v['name'],'url':v['url']} for v in out.values()]
def rentbuy(offers,rent,buy,wurl):
  r={x['name']:x for x in group(offers,rent,{'LeaseOut'},wurl)}
  b={x['name']:x for x in group(offers,buy,{'Sell'},wurl)}
  return [{'name':n,'url':(r.get(n) or {}).get('url') or (b.get(n) or {}).get('url')} for n in list(r)+[k for k in b if k not in r]]
def parse_g1_options(s):
  s=(s or '').strip().rstrip('.')
  if not s or s.lower().startswith('no confirmed') or 'not verified' in s.lower(): return [],[]
  sub,rb=[],[]
  for part in [x.strip() for x in s.split(';') if x.strip()]:
    m=re.match(r'(?i)(rent/buy|rent|buy|free)\s*:\s*(.*)',part)
    if m: rb+=split_names(m.group(2)) if m.group(1).lower()!='free' else []
    else: sub.append(part)
  return sub,rb
def watch(row2,wurl,g1opts=None):
  rec=jwrec(wurl) if wurl else None; offers=rec['offers'] if rec else []
  if row2:
    return {'stream':group(offers,split_names(row2['subscription_services']),{'ProvideService'},wurl),
            'free':group(offers,split_names(row2['free_services']),{'ProvideService'},wurl),
            'rentbuy':rentbuy(offers,split_names(row2['rental_services']),split_names(row2['purchase_services']),wurl)}
  sub,rb=parse_g1_options(g1opts)
  rn=sorted({o['name'] for o in offers if o['fn']=='LeaseOut'}) or rb
  bn=sorted({o['name'] for o in offers if o['fn']=='Sell'}) or rb
  return {'stream':group(offers,sub,{'ProvideService'},wurl),'free':[],'rentbuy':rentbuy(offers,rn,bn,wurl)}

# ---------- posters ----------
manifest={}
def fid(title,year): return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',norm(title))).strip('-')+'-'+str(year)
def poster(title,year,*cands):
  # JustWatch images first (s332); other direct image URLs as a fallback. Returns the first file that is on disk.
  cands=sorted([u for u in cands if u],key=lambda u:'images.justwatch.com/poster/' not in u)
  first=None
  for u in cands:
    if 'images.justwatch.com/poster/' in u:
      u=re.sub(r'/s\d+/','/s332/',u); name=u.rstrip('/').split('/')[-1]
      if not name.endswith('.jpg'): name+='.jpg'
    elif re.search(r'\.(jpe?g|png|webp)(\?|$)',u,re.I) or any(h in u for h in ('mzstatic.com','images.plex.tv','nflxso.net','img.usheru.com','imageapi.')):
      name=fid(title,year)+'.jpg'
    else: continue
    if first is None: first=name; manifest.setdefault(name,u)
    if os.path.exists(f'{P}/posters/{name}'): return 'posters/'+name
  return None

# ---------- guide 2 index ----------
by_key={}; by_url={}
for r in g2:
  by_key.setdefault((norm(r['title']),r['year']),r)
  if r['us_watch_url']: by_url.setdefault(r['us_watch_url'],r)
origin_list=lambda s:[x.strip() for x in s.split(';') if x.strip()]
def g1_origin(r):
  r2=by_key.get((norm(r['original_title_and_english_title']),r['release_year'])) or by_url.get(r['us_watch_url'])
  if r2: return r2,origin_list(r2['country_of_origin']),'doc'
  rec=jwrec(r['us_watch_url'])
  o=rec and rec.get('origin')
  if isinstance(o,list): o=o[0] if o else None
  if isinstance(o,dict): o=o.get('name')
  o={'USA':'United States','US':'United States','United States of America':'United States','UK':'United Kingdom'}.get(o,o)
  return None,([o] if o else []),('justwatch' if o else 'unknown')

report=collections.defaultdict(list)
# ---------- trailers (Matt's CSV, researched 26 Nov 2026), matched by normalised title + year ----------
TRAILER={}
if C3:
  C3ROWS=list(csv.DictReader(open(C3,encoding='utf-8-sig')))
  for r in C3ROWS:
    t=r.get('title') or r.get('original_title_and_english_title') or ''; y=r.get('year') or r.get('release_year') or ''
    if r['trailer_url'].strip():
      TRAILER.setdefault((norm(t),y),{'url':r['trailer_url'].strip(),'platform':r['trailer_platform'].strip()})
else: C3ROWS=[]
trailer_hits=set()
def trailer(title,year):
  t=TRAILER.get((norm(title),str(year)))
  if t: trailer_hits.add((norm(title),str(year)))
  else: report['no trailer'].append(f'{title} ({year})')
  return t

def market_shell(name):
  iso=ISO[name]; p=FEAT.get(iso)
  lat,lng=EXTRA_POS.get(iso) or (p['ly'],p['lx'])
  dn=DISPLAY.get(name,name)
  return iso,{'name':dn,'code':SHORT.get(dn,SHORT.get(name,dn)),'the':dn in THE or name in THE,'lat':lat,'lng':lng}

markets={}
# ---------- US movies mode (guide 1) ----------
rows=collections.defaultdict(list)
for r in g1:
  if r['audience_market'] in SKIP_MARKETS: continue
  rows[r['audience_market']].append(r)
for name,rs in rows.items():
  iso,shell=market_shell(name); films=[]
  for r in sorted(rs,key=lambda r:int(r['rank'])):
    t=r['original_title_and_english_title']; r2,origin,osrc=g1_origin(r)
    # Global Top 10 mode (Matt, 26 Nov 2026): every film in the country's Top 10, wherever it was made
    if osrc=='unknown': report['origin unknown (shown as "Origin not recorded")'].append(f'{name}: {t}')
    rating=r['us_tv_rating'] if r['us_rating_filter']=='TV rating only' else r['us_rating_filter']
    # prefer the guide-2 row's JustWatch page when this row's own link has none (e.g. a year-verified slug match)
    wurl=r2['us_watch_url'] if r2 and not jwrec(r['us_watch_url']) and jwrec(r2['us_watch_url']) else r['us_watch_url']
    films.append({'pos':int(r['rank']),'title':t,'year':int(r['release_year']),'min':int(r['runtime_minutes']),
      'rating':rating or 'Unverified','usr':r['us_mpa_rating'] or r['us_tv_rating'],'cert':r['rating_certificate'],
      'index':float(r['index']) if r['index'] else None,'origin':origin,'originSrc':osrc,
      'poster':poster(t,r['release_year'],r['poster_or_image_url'],(jwrec(wurl) or {}).get('image')),
      'trailer':trailer(t,r['release_year']),'jw':jwlink(wurl,t),'watch':{'US':watch(r2,wurl,r['us_watch_options'])}})
  m=markets.setdefault(iso,shell)
  m['us']={'sources':'National + Netflix + JustWatch index','films':films}
  if not films: report['guide-1 market with no US-made films'].append(name)

# ---------- Country specific mode (guide 2) ----------
AUTH_CUT=[' via ',' recorded by',' certificate',' current classification',' local distributor listing',' educational distributor listing',' distributor label',' Ministry of Justice',' rating']
AUTH_NAME={'British Columbia classification':'BC classification','Italian classification':'Italian classification','New Zealand':'NZ distributor label','Australian':'Australian Classification'}
def clean_auth(a):
  a=a.strip()
  if not a: return ''
  for c in AUTH_CUT:
    i=a.find(c)
    if i>0: a=a[:i]
  return AUTH_NAME.get(a.strip(),a.strip())
AGE={'U':0,'G':0,'A':0,'T':0,'Tous publics':0,'A/i':0,'PG':8,'M':15,'MA 15+':15,'12A':12,'18A':18,'R':17,'PG-13':13}
def age(r):
  if r in AGE: return AGE[r]
  m=re.search(r'\d+',r); return int(m.group()) if m else 99
def strip_auth(rating,auth):
  for a in (auth,auth.split()[0] if auth else ''):
    if a and rating.startswith(a+' '): return rating[len(a)+1:]
  return rating
loc=collections.defaultdict(list)
for r in g2: loc[r['country']].append(r)
for name in sorted(loc,key=lambda n:n=='Soviet Union'):   # Russia's own films first, then the Soviet-era ones
  rs=loc[name]; iso,shell=market_shell(name)
  m=markets.setdefault(iso,shell)
  L=m.setdefault('local',{'authority':'','scale':[],'films':[]})
  auths=collections.Counter(clean_auth(r['rating_authority']) for r in rs if r['country_rating']!='Unverified' and r['rating_authority'].strip())
  if auths and not L['authority']: L['authority']=auths.most_common(1)[0][0]
  for r in sorted(rs,key=lambda r:int(r['catalogue_position'])):
    a=clean_auth(r['rating_authority']) or L['authority']
    rating=strip_auth(r['country_rating'],a) if r['country_rating']!='Unverified' else 'Unverified'
    f={'pos':len(L['films'])+1,'title':r['title'],'year':int(r['year']),'min':int(r['runtime_minutes']),'rating':rating,
       'hot':rating!='Unverified' and age(rating)>=15,'authority':a,'usr':r['us_mpa_rating'] or r['us_tv_rating'] or '',
       'origin':origin_list(r['country_of_origin']),'originSrc':'doc','ratingSrc':r['rating_source'],
       'poster':poster(r['title'],r['year'],r['poster_or_image_url'],(jwrec(r['us_watch_url']) or {}).get('image')),
       'trailer':trailer(r['title'],r['year']),'jw':jwlink(r['us_watch_url'],r['title']),'watch':{'US':watch(r,r['us_watch_url'])}}
    if name=='Soviet Union': f['era']='Soviet Union'
    L['films'].append(f)
  L['scale']=sorted({f['rating'] for f in L['films'] if f['rating']!='Unverified'},key=lambda x:(age(x),x))

# ---------- films only in the guide's poster index (entry_type poster_index_only in the all-entries CSV) ----------
# They belong to no country list. Each joins the Country specific list of the country JustWatch says made it
# (decided by Matt, 26 Nov 2026: all five are US-made, so they follow the US list's 10), flagged as origin per JustWatch.
for r in [r for r in C3ROWS if r.get('entry_type')=='poster_index_only']:
  t=r['title'] or r['original_title_and_english_title']; y=r['year'] or r['release_year']
  rec=jwrec(r['us_watch_url']); o=rec and rec.get('origin')
  if isinstance(o,list): o=o[0] if o else None
  iso=ISO.get(o) if o else None
  if not iso or iso not in markets or 'local' not in markets[iso]:
    report['poster-index film not placed'].append(f'{t} ({y}): origin {o!r}'); continue
  L=markets[iso]['local']; auth=L['authority']
  rating=(r['us_mpa_rating'] if auth=='MPA' and r['us_mpa_rating'] else 'Unverified')
  L['films'].append({'pos':len(L['films'])+1,'title':t,'year':int(y),'min':int(r['runtime_minutes']),'rating':rating,
     'hot':False,'authority':auth,'usr':r['us_mpa_rating'] or r['us_tv_rating'] or '','origin':[o],'originSrc':'justwatch',
     'ratingSrc':r['rating_source'],'poster':poster(t,y,r['poster_or_image_url'],(rec or {}).get('image')),
     'trailer':trailer(t,y),'jw':jwlink(r['us_watch_url'],t),'watch':{'US':watch(None,r['us_watch_url'],r['us_watch_options'])},'source':'poster index'})
  L['scale']=sorted({f['rating'] for f in L['films'] if f['rating']!='Unverified'},key=lambda x:(age(x),x))
  report['poster-index film added'].append(f'{t} ({y}) -> {iso} Country specific #{len(L["films"])}')

# ---------- write ----------
json.dump(markets,open(P+'/data/markets.json','w'),ensure_ascii=False,separators=(',',':'))
json.dump(manifest,open(os.path.join(HERE,'posters_manifest.json'),'w'),indent=1,ensure_ascii=False)
has=lambda iso,k: bool(markets.get(iso,{}).get(k,{}).get('films'))
for f in geo['features']:
  p=f['properties']
  p['st']='has' if has(p['iso'],'us') else 'none'
  p['lo']='has' if has(p['iso'],'local') else 'none'
json.dump(geo,open(P+'/data/countries.json','w'),separators=(',',':'))

# ---------- report ----------
shapes={f['properties']['iso'] for f in geo['features']}
print('markets:',len(markets),'| with US movies:',sum(has(i,'us') for i in markets),'| with Country specific:',sum(has(i,'local') for i in markets))
print('globe shapes with films  US:',sum(f['properties']['st']=='has' for f in geo['features']),' local:',sum(f['properties']['lo']=='has' for f in geo['features']))
print('markets without a shape:',sorted(i for i in markets if i not in shapes))
films=[x for m in markets.values() for k in ('us','local') for x in m.get(k,{}).get('films',[])]
print('film rows:',len(films),'| JustWatch origin:',sum(x['originSrc']=='justwatch' for x in films),'| no poster:',sum(not x['poster'] for x in films),'| no offers:',sum(not any(x['watch']['US'].values()) for x in films))
for k,v in report.items(): print(k,len(v)); [print('   ',x) for x in sorted(set(v))]
for iso,m in sorted(markets.items()):
  L=m.get('local')
  if L: print(f"  {iso} {m['name']}: authority={L['authority']!r} scale={L['scale']}")
