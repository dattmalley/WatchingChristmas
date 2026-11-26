# Fetches JustWatch US movie pages and extracts JSON-LD WatchAction direct links, countryOfOrigin and the poster image.
# Usage:
#   python3 -I scripts/fetch_justwatch_offers.py CACHE.json <slug> [<slug> ...]
#   python3 -I scripts/fetch_justwatch_offers.py CACHE.json --from-csv source/Holiday-Films-US-Ratings.csv source/Holiday-Films-by-Country-of-Origin.csv
#   slug = last part of a us_watch_url, e.g. https://www.justwatch.com/us/movie/elf -> elf
# CACHE.json is read first and merged: slugs already cached are not fetched again (about 1 request per second).
import sys,json,re,urllib.request,time,os,csv
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
JW='https://www.justwatch.com/us/movie/'
cache_path=sys.argv[1]
out=json.load(open(cache_path)) if os.path.exists(cache_path) else {}
if sys.argv[2:3]==['--from-csv']:
  slugs=[]
  for p in sys.argv[3:]:
    for r in csv.DictReader(open(p,encoding='utf-8-sig')):
      u=(r.get('us_watch_url') or '').strip()
      if u.startswith(JW):
        s=u.rstrip('/').split('/')[-1]
        if s not in slugs: slugs.append(s)
else: slugs=sys.argv[2:]
def parse(html):
  offers=[];origin=None;image=None
  for blk in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>',html,re.S):
    try: d=json.loads(blk)
    except Exception: continue
    for it in (d.get('@graph',[d]) if isinstance(d,dict) else d):
      if not isinstance(it,dict): continue
      if it.get('countryOfOrigin') and not origin: origin=it['countryOfOrigin']
      if it.get('image') and not image:
        im=it['image']; im=im[0] if isinstance(im,list) else im
        image=im.get('url') if isinstance(im,dict) else im
      for a in it.get('potentialAction') or []:
        tg=a.get('target') or {}; tg=tg[0] if isinstance(tg,list) and tg else tg
        if a.get('@type')!='WatchAction' or not isinstance(tg,dict) or not tg.get('urlTemplate'): continue
        o=a.get('expectsAcceptanceOf') or {}; o=o[0] if isinstance(o,list) else o
        by=o.get('offeredBy') or {}
        offers.append({'name':by.get('name') if isinstance(by,dict) else str(by),'url':tg['urlTemplate'],'fn':(o.get('businessFunction') or '').split('#')[-1],'price':o.get('price')})
  if not image:
    m=re.search(r'<meta property="og:image" content="([^"]+)"',html); image=m.group(1) if m else None
  return origin,offers,image
todo=[s for s in slugs if s not in out or 'image' not in out[s]]
print(f'{len(slugs)} slugs, {len(todo)} to fetch',flush=True)
for s in todo:
  try:
    html=urllib.request.urlopen(urllib.request.Request(JW+s,headers={'User-Agent':UA}),timeout=40).read().decode('utf-8','ignore')
    origin,offers,image=parse(html)
    out[s]={'origin':origin,'offers':offers,'image':image}
    print(s,'origin:',json.dumps(origin)[:80],'offers:',len(offers),'image:',bool(image),flush=True)
  except Exception as e:
    print(s,'FAILED',e,flush=True)
  json.dump(out,open(cache_path,'w'),indent=1,ensure_ascii=False)
  time.sleep(1)
json.dump(out,open(cache_path,'w'),indent=1,ensure_ascii=False)
