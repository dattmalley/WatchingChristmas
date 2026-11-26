# Downloads every poster listed in scripts/posters_manifest.json (written by build_markets.py) into site/posters/.
# JustWatch posters are requested at the s332 size. Files already on disk are skipped.
# Usage: python3 -I scripts/fetch_posters.py scripts/posters_manifest.json site/posters
import sys,json,os,time,urllib.request
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
man=json.load(open(sys.argv[1])); out=sys.argv[2]; os.makedirs(out,exist_ok=True)
ok=skip=bad=0
for name,url in man.items():
  path=os.path.join(out,name)
  if os.path.exists(path): skip+=1; continue
  try:
    res=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=40)
    ctype=res.headers.get('Content-Type',''); data=res.read()
    if not ctype.startswith('image/') or len(data)<2000: raise ValueError(f'not an image ({ctype}, {len(data)} bytes)')
    open(path,'wb').write(data); ok+=1; print('ok ',name,len(data)//1024,'KB',flush=True)
  except Exception as e:
    bad+=1; print('BAD',name,url,e,flush=True)
  time.sleep(.4)
print(f'downloaded {ok}, already had {skip}, failed {bad}')
