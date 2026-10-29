"""Matchs à venir. Sources (vérifiées depuis la box le 28/10/2026) :
 1. ESPN (API publique non officielle, SANS clé) : calendrier, coup d'envoi UTC, stade+ville, cotes moneyline (DraftKings).
 2. football-data.org v4 : nécessite FOOTBALL_DATA_API_KEY (code prêt ; pas de cotes dans l'offre gratuite).
 3. OpenLigaDB (sans clé, Bundesliga/2.Bundesliga/DFB-Pokal uniquement, pas de stade ni de cotes) : secours.
"""
import os, time, threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import requests

ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard"
# slug ESPN -> (nom FR, coupe à élimination directe ?)
LEAGUES = {
    'fra.1': ("Ligue 1", False), 'eng.1': ("Premier League", False), 'esp.1': ("LaLiga", False),
    'ger.1': ("Bundesliga", False), 'ita.1': ("Serie A", False), 'por.1': ("Liga Portugal", False),
    'ned.1': ("Eredivisie", False), 'bel.1': ("Pro League (Belgique)", False),
    'uefa.champions': ("Ligue des champions", None), 'uefa.europa': ("Ligue Europa", None),
    'uefa.europa.conf': ("Ligue Europa Conférence", None),
    'fra.coupe_de_france': ("Coupe de France", True), 'eng.fa': ("FA Cup", True),
    'eng.league_cup': ("Coupe de la Ligue (Angleterre)", True), 'esp.copa_del_rey': ("Copa del Rey", True),
    'ger.dfb_pokal': ("DFB-Pokal", True), 'ita.coppa_italia': ("Coupe d'Italie", True),
}
KO_WORDS = ('round of', 'quarter', 'semi', 'final', 'knockout', 'play-off', 'playoff', 'last 16', '1/8', '1/4')
_cache = {}
_lock = threading.Lock()
TTL = int(os.environ.get('FIXTURES_TTL', 900))


def american_to_decimal(s):
    try:
        v = float(str(s).replace('+', ''))
    except Exception:
        return None
    if v == 0:
        return None
    return round(1 + v / 100, 2) if v > 0 else round(1 + 100 / abs(v), 2)


def favourite_from_odds(home, away, tol=1.10):
    """-> 'a' (domicile) | 'b' (extérieur) | 'egal' | None. Seuil [HYP] : rapport des cotes < 1,10 => presque égal."""
    if not home or not away:
        return None
    if max(home, away) / min(home, away) < tol:
        return 'egal'
    return 'a' if home < away else 'b'


def _parse_espn(ev, slug):
    comp = ev['competitions'][0]
    st = ev.get('status', {}).get('type', {})
    if st.get('state') != 'pre':
        return None
    cs = {c['homeAway']: c for c in comp['competitors']}
    if 'home' not in cs or 'away' not in cs:
        return None
    v = comp.get('venue') or ev.get('venue') or {}
    addr = v.get('address') or {}
    odds = None
    for o in comp.get('odds') or []:
        ml = o.get('moneyline') or {}
        def pick(side):
            x = ml.get(side) or {}
            return (x.get('close') or {}).get('odds') or (x.get('open') or {}).get('odds')
        h, d, a = (american_to_decimal(pick(k)) for k in ('home', 'draw', 'away'))
        if h and a:
            odds = dict(home=h, draw=d, away=a, fournisseur=(o.get('provider') or {}).get('displayName', 'ESPN'))
            break
    name, ko_default = LEAGUES.get(slug, (slug, None))
    headline = ' '.join([(n.get('headline') or '') for n in comp.get('notes', [])] + [ev.get('name', '')]).lower()
    ko = ko_default if ko_default is not None else any(w in headline for w in KO_WORDS)
    return dict(
        id=f"espn:{ev['id']}", source='ESPN', competition=name, slug=slug,
        home=cs['home']['team']['displayName'], away=cs['away']['team']['displayName'],
        kickoff_utc=ev['date'].replace('Z', '').replace('T', ' ')[:16], venue=v.get('fullName'),
        city=addr.get('city'), country=addr.get('country'), knockout=bool(ko), odds=odds,
        favorite=favourite_from_odds(odds['home'], odds['away']) if odds else None)


def _espn_day(slug, day):
    try:
        r = requests.get(ESPN.format(slug=slug), params={'dates': day}, timeout=12)
        if r.status_code != 200:
            return []
        return [m for m in (_parse_espn(e, slug) for e in r.json().get('events', [])) if m]
    except Exception:
        return []


def from_espn(days=7):
    today = datetime.now(timezone.utc).date()
    jobs = [(s, (today + timedelta(days=i)).strftime('%Y%m%d')) for s in LEAGUES for i in range(days + 1)]
    with ThreadPoolExecutor(16) as ex:
        res = list(ex.map(lambda a: _espn_day(*a), jobs))
    out = {}
    for lst in res:
        for m in lst:
            out[m['id']] = m
    return list(out.values())


def from_football_data(key, days=7):
    """Code prêt à l'emploi : activé si FOOTBALL_DATA_API_KEY est défini. (Non testé sans clé valide.)"""
    today = datetime.now(timezone.utc).date()
    r = requests.get("https://api.football-data.org/v4/matches", headers={'X-Auth-Token': key},
                     params={'dateFrom': today.isoformat(), 'dateTo': (today + timedelta(days=days)).isoformat()}, timeout=15)
    r.raise_for_status()
    out = []
    for m in r.json().get('matches', []):
        if m.get('status') not in ('SCHEDULED', 'TIMED'):
            continue
        stage = (m.get('stage') or '')
        ko = stage not in ('REGULAR_SEASON', 'LEAGUE_STAGE', 'GROUP_STAGE', '')
        out.append(dict(id=f"fd:{m['id']}", source='football-data.org', competition=m['competition']['name'], slug=m['competition'].get('code'),
                        home=m['homeTeam'].get('name'), away=m['awayTeam'].get('name'),
                        kickoff_utc=m['utcDate'].replace('Z', '').replace('T', ' ')[:16], venue=m.get('venue'), city=None, country=None,
                        knockout=ko, odds=None, favorite=None))
    return out


def from_openligadb(days=7):
    out = []
    now = datetime.now(timezone.utc)
    for lg in ('bl1', 'bl2', 'dfb'):
        try:
            r = requests.get(f"https://api.openligadb.de/getmatchdata/{lg}", timeout=12)
            for m in r.json():
                dt = datetime.strptime(m['matchDateTimeUTC'][:16], "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
                if m.get('matchIsFinished') or not (now <= dt <= now + timedelta(days=days + 1)):
                    continue
                loc = m.get('location') or {}
                out.append(dict(id=f"oldb:{m['matchID']}", source='OpenLigaDB', competition=m['leagueName'].split(' 20')[0], slug=lg,
                                home=m['team1']['teamName'], away=m['team2']['teamName'],
                                kickoff_utc=dt.strftime('%Y-%m-%d %H:%M'), venue=loc.get('locationStadium'), city=loc.get('locationCity'), country='Allemagne',
                                knockout=(lg == 'dfb'), odds=None, favorite=None))
        except Exception:
            pass
    return out


def get_matches(days=7, force=False):
    """-> dict(matches, sources[{nom, ok, nb, note}], auto: bool)"""
    key = ('m', days)
    with _lock:
        c = _cache.get(key)
        if c and not force and time.time() - c['t'] < TTL:
            return c['v']
    sources, matches = [], []
    try:
        m = from_espn(days)
        sources.append(dict(nom='ESPN (sans clé)', ok=bool(m), nb=len(m), note="Calendrier, stade et cotes (DraftKings) — API publique non officielle, peut changer sans préavis."))
        matches += m
    except Exception as e:
        sources.append(dict(nom='ESPN (sans clé)', ok=False, nb=0, note=str(e)[:100]))
    fdk = os.environ.get('FOOTBALL_DATA_API_KEY')
    if fdk:
        try:
            m = from_football_data(fdk, days)
            have = {(x['home'][:5].lower(), x['kickoff_utc'][:10]) for x in matches}
            m = [x for x in m if (x['home'][:5].lower(), x['kickoff_utc'][:10]) not in have]
            sources.append(dict(nom='football-data.org (clé)', ok=True, nb=len(m), note="Matchs ajoutés (non déjà présents via ESPN)."))
            matches += m
        except Exception as e:
            sources.append(dict(nom='football-data.org (clé)', ok=False, nb=0, note=f"Erreur : {str(e)[:100]}"))
    else:
        sources.append(dict(nom='football-data.org', ok=False, nb=0, note="Désactivé : définir FOOTBALL_DATA_API_KEY pour l'activer."))
    if not matches:
        m = from_openligadb(days)
        sources.append(dict(nom='OpenLigaDB (secours)', ok=bool(m), nb=len(m), note="Bundesliga / DFB-Pokal seulement, sans stade ni cotes."))
        matches += m
    matches.sort(key=lambda x: (x['kickoff_utc'], x['competition']))
    v = dict(matches=matches, sources=sources, auto=bool(matches), maj=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))
    with _lock:
        _cache[key] = dict(t=time.time(), v=v)
    return v
