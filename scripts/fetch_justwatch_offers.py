# Fetches JustWatch US movie pages and extracts JSON-LD WatchAction direct links plus countryOfOrigin.
# Usage: python3 -I scripts/fetch_justwatch_offers.py OUT.json <justwatch-slug> [<slug> ...]
#   slug = last part of a us_watch_url, e.g. https://www.justwatch.com/us/movie/elf -> elf
import sys,json,re,urllib.request,time
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
slugs=sys.argv[2:]; out={}
for s in slugs:
  html=urllib.request.urlopen(urllib.request.Request('https://www.justwatch.com/us/movie/'+s,headers={'User-Agent':UA}),timeout=40).read().decode('utf-8','ignore')
  offers=[];origin=None
  for blk in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>',html,re.S):
    try: d=json.loads(blk)
    except Exception: continue
    for it in (d.get('@graph',[d]) if isinstance(d,dict) else d):
      if not isinstance(it,dict): continue
      if it.get('countryOfOrigin') and not origin: origin=it['countryOfOrigin']
      for a in it.get('potentialAction') or []:
        if a.get('@type')!='WatchAction': continue
        o=a.get('expectsAcceptanceOf') or {}; o=o[0] if isinstance(o,list) else o
        by=o.get('offeredBy') or {}
        offers.append({'name':by.get('name') if isinstance(by,dict) else str(by),'url':a['target']['urlTemplate'],'fn':(o.get('businessFunction') or '').split('#')[-1],'price':o.get('price')})
  out[s]={'origin':origin,'offers':offers}; print(s,'origin:',json.dumps(origin)[:120],'offers:',len(offers)); time.sleep(1)
json.dump(out,open(sys.argv[1],'w'),indent=1)
