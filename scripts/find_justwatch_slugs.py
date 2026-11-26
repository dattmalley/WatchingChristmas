# For guide-2 films with no working JustWatch US page, tries likely JustWatch slugs (English and original title,
# with and without the year) and keeps a page only when its release year equals the guide's year.
# Usage: python3 -I scripts/find_justwatch_slugs.py source/Holiday-Films-by-Country-of-Origin.csv scripts/justwatch_offers.json scripts/justwatch_slug_matches.json
import csv,json,re,sys,time,unicodedata,urllib.request,os
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
JWP='https://www.justwatch.com/us/movie/'
g2=list(csv.DictReader(open(sys.argv[1],encoding='utf-8-sig'))); jw=json.load(open(sys.argv[2]))
out=json.load(open(sys.argv[3])) if os.path.exists(sys.argv[3]) else {}
def sl(t):
  t=unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode().lower().replace("'",'').replace('’','')
  return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',t)).strip('-')
def page_year(s):
  try: h=urllib.request.urlopen(urllib.request.Request(JWP+s,headers={'User-Agent':UA}),timeout=30).read().decode('utf-8','ignore')
  except Exception: return None
  m=re.search(r'"dateCreated":"(\d{4})',h) or re.search(r'"datePublished":"(\d{4})',h)
  return m.group(1) if m else None
seen=set()
for r in g2:
  key=f"{r['title']}|{r['year']}"
  u=r['us_watch_url']; s=u.rstrip('/').split('/')[-1] if u.startswith(JWP) else None
  if (s and s in jw) or key in out or key in seen: continue
  seen.add(key)
  m=re.match(r'(.*?)\s*\((.*)\)\s*$',r['title']); names=[m.group(2),m.group(1)] if m else [r['title']]
  cands=[]
  for n in names: cands+= [sl(n), sl(n)+'-'+r['year']]
  hit=None
  for c in dict.fromkeys(cands):
    y=page_year(c); time.sleep(1)
    if y==r['year']: hit=c; break
  out[key]=hit; print(key,'->',hit,flush=True)
json.dump(out,open(sys.argv[3],'w'),indent=1,ensure_ascii=False)
