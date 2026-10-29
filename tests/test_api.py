"""pytest : tests fonctionnels de l'API (sans réseau obligatoire sauf géocodage Nominatim -> repli liste intégrée)."""
import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from app.main import app
from app import geo
c = TestClient(app)
base = dict(equipe_a='PSG', equipe_b='OM', favori='a', stade='Parc des Princes', ville='Paris', pays='France')

def test_dst_summer_and_winter():
    u, i = geo.local_to_utc('2026-07-12', '21:00', 'Europe/Paris'); assert u.hour == 19 and i['offset_h'] == 2
    u, i = geo.local_to_utc('2026-12-12', '21:00', 'Europe/Paris'); assert u.hour == 20 and i['offset_h'] == 1
    u, i = geo.local_to_utc('2026-03-29', '02:30', 'Europe/Paris'); assert i['avertissements']          # heure inexistante
    u, i = geo.local_to_utc('2026-10-25', '02:30', 'Europe/Paris'); assert i['avertissements']          # heure ambiguë

def test_tz_lookup():
    assert geo.tz_for(48.84, 2.25) == 'Europe/Paris'
    assert geo.tz_for(-33.87, 151.21) == 'Australia/Sydney'

def test_predict_full():
    r = c.post('/api/predict', json=dict(base, date='2026-11-01', heure='21:00'))
    assert r.status_code == 200
    j = r.json()
    assert j['prediction']['resultat'] in ('a', 'b', 'nul')
    assert j['match']['coup_denvoi_utc'] == '2026-11-01 20:00'     # CET = UTC+1 le 1er nov. 2026
    assert 0 <= j['theme']['asc']['lon'] < 360 and j['prediction']['confiance'] in ('élevée', 'moyenne', 'faible')
    assert isinstance(j['temoignages'], list)

def test_equal_favourites_is_undetermined():
    j = c.post('/api/predict', json=dict(base, favori='egal', date='2026-11-01', heure='21:00')).json()
    assert j['prediction']['resultat'] == 'indetermine' and not j['prediction']['methode_utilisable'] and j['temoignages'] == []

def test_kickoff_utc_equivalent():
    a = c.post('/api/predict', json=dict(base, date='2026-11-01', heure='21:00')).json()
    b = c.post('/api/predict', json=dict(base, kickoff_utc='2026-11-01 20:00')).json()
    assert a['theme']['asc'] == b['theme']['asc'] and a['prediction']['resultat'] == b['prediction']['resultat']

def test_validation_errors():
    assert c.post('/api/predict', json=dict(base, favori='x', date='2026-11-01', heure='21:00')).status_code == 422
    assert c.post('/api/predict', json=dict(equipe_a='a', equipe_b='b', favori='a', date='2026-11-01', heure='21:00')).status_code == 422  # pas de lieu
    assert c.post('/api/predict', json=dict(base, date='2026-13-01', heure='21:00')).status_code == 422

def test_latlon_input():
    j = c.post('/api/predict', json=dict(equipe_a='A', equipe_b='B', favori='b', date='2026-11-01', heure='21:00', lat=51.55, lon=-0.108)).json()
    assert j['match']['fuseau'] == 'Europe/London' and j['match']['coup_denvoi_utc'] == '2026-11-01 21:00'

def test_cases_endpoint():
    assert len(c.get('/api/cases').json()) == 25
