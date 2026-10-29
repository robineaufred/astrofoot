import sys,time; sys.path.insert(0,'.')
from app.engine.judge_fr import judge
from app.engine.cases import CASES,utc
ok=0; t0=time.time()
for c in CASES:
    j=judge(utc(c),c['lat'],c['lon'],c['sport'])
    r=(j['result']=='F'); ok+=(r==c['fav_wins'])
    print(c['id'],'OK' if r==c['fav_wins'] else 'KO',j['result'],j['decided_tier'])
print(ok,len(CASES),time.time()-t0)
