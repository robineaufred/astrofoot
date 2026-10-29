#!/usr/bin/env python3
"""Exécute les 25 cas du livre via POST /api/predict et rapporte le score.
Usage : ve/bin/python tests/run_book_cases.py [URL]   (défaut http://localhost:8000 ; 'inproc' = sans serveur)
Les 25 cas ont servi à RÉGLER les poids : ce n'est PAS une validation hors échantillon."""
import sys, re
sys.path.insert(0, '.')
from app.engine.cases import CASES

target = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8000'
if target == 'inproc':
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app); post = lambda p: c.post('/api/predict', json=p)
else:
    import requests
    post = lambda p: requests.post(target + '/api/predict', json=p, timeout=60)

ok = 0; bad = []; score_ok = 0; score_n = 0
for cs in CASES:
    d, h = cs['dt'].split()
    r = post(dict(equipe_a=cs['name'].split(' v ')[0].split(' (fav)')[0], equipe_b='Outsider', favori='a', date=d, heure=h, lat=cs['lat'], lon=cs['lon'],
                  utc_offset=cs['tz'], sport=cs['sport'], elimination=cs['sport'].endswith('et')))
    assert r.status_code == 200, (cs['id'], r.text)
    j = r.json(); res = j['prediction']['resultat']
    good = (res == 'a') == cs['fav_wins']
    ok += good
    if not good: bad.append(cs['id'])
    m = re.search(r'(\d+)-(\d+)', cs['score'])
    sc = j['prediction']['score']
    note = ''
    if cs['sport'].startswith('foot') and m:
        a, b = int(m.group(1)), int(m.group(2))
        win, lose = max(a, b), min(a, b)
        pa, pb = sc['a'], sc['b']
        g = (max(pa, pb), min(pa, pb)) == (win, lose) and ((pa > pb) == (not cs['fav_wins']) or True)
        exact = (max(pa, pb), min(pa, pb)) == (win, lose) and ((res == 'a') == cs['fav_wins'])
        score_n += 1; score_ok += exact; note = f" score prédit {pa}-{pb} (livre: {cs['score']}) {'✓' if exact else '✗'}"
    print(f"{cs['id']:4} {'OK' if good else 'KO'}  prédit={'favori' if res=='a' else 'outsider'} niveau={j['prediction']['niveau_decisif']} conf={j['prediction']['confiance']}{note}")
print(f"\nVAINQUEUR : {ok}/{len(CASES)}  (échecs : {', '.join(bad) or 'aucun'})  — réglé sur ces mêmes cas, non indépendant")
print(f"SCORE EXACT (foot, matchs avec score) : {score_ok}/{score_n} — indicatif")
print("Référence « toujours favori » :", sum(1 for c in CASES if c['fav_wins']), f"/{len(CASES)}")
