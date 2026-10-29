"""Géocodage (Nominatim + cache disque + liste intégrée de secours) et conversion heure locale -> UTC."""
import json, os, threading, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
from timezonefinder import TimezoneFinder
from .venues import lookup, norm

DATA = Path(os.environ.get('FRAWLEY_DATA_DIR', Path(__file__).resolve().parent.parent / 'data'))
DATA.mkdir(exist_ok=True)
CACHE_FILE = DATA / 'geocache.json'
NOMINATIM = os.environ.get('NOMINATIM_URL', 'https://nominatim.openstreetmap.org/search')
UA = os.environ.get('NOMINATIM_USER_AGENT', 'frawley-sports-astrology-app/1.0 (educational, contact: set NOMINATIM_USER_AGENT)')
_lock = threading.Lock()
_last_call = [0.0]
_tf = None
_cache = None


def _tzf():
    global _tf
    if _tf is None:
        _tf = TimezoneFinder()
    return _tf


def _load():
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(CACHE_FILE.read_text())
        except Exception:
            _cache = {}
    return _cache


def _save():
    try:
        CACHE_FILE.write_text(json.dumps(_cache, ensure_ascii=False, indent=1))
    except Exception:
        pass


def tz_for(lat, lon):
    return _tzf().timezone_at(lat=lat, lng=lon) or _tzf().closest_timezone_at(lat=lat, lng=lon)


def geocode(venue=None, city=None, country=None):
    """-> dict(lat, lon, tz, nom, source) ; source ∈ cache | nominatim | liste_integree. Lève LookupError si introuvable."""
    parts = [p for p in (venue, city, country) if p]
    if not parts:
        raise LookupError("Aucun lieu fourni")
    key = norm(' '.join(parts))
    with _lock:
        c = _load()
        if key in c:
            r = dict(c[key]); r['source'] = 'cache'
            return r
    queries = []
    if venue and city:
        queries.append(f"{venue}, {city}" + (f", {country}" if country else ""))
    if venue:
        queries.append(venue + (f", {country}" if country else ""))
    if city:
        queries.append(city + (f", {country}" if country else ""))
    err = None
    for q in queries:
        try:
            with _lock:   # Nominatim : 1 requête/s max (politique d'usage)
                wait = 1.1 - (time.time() - _last_call[0])
                if wait > 0:
                    time.sleep(wait)
                _last_call[0] = time.time()
            r = requests.get(NOMINATIM, params=dict(q=q, format='json', limit=1, addressdetails=0),
                             headers={'User-Agent': UA, 'Accept-Language': 'fr'}, timeout=8)
            if r.status_code == 200 and r.json():
                j = r.json()[0]
                lat, lon = float(j['lat']), float(j['lon'])
                out = dict(lat=lat, lon=lon, tz=tz_for(lat, lon), nom=j.get('display_name', q)[:160], source='nominatim')
                with _lock:
                    _load()[key] = {k: out[k] for k in ('lat', 'lon', 'tz', 'nom')}
                    _save()
                return out
            err = f"Nominatim HTTP {r.status_code}"
        except Exception as e:
            err = f"Nominatim indisponible ({type(e).__name__})"
    b = lookup(venue, city, *(parts))
    if b:
        return dict(lat=b['lat'], lon=b['lon'], tz=b['tz'], nom=b['label'] + ' (liste intégrée)', source='liste_integree')
    raise LookupError(f"Lieu introuvable : {', '.join(parts)} ({err or 'aucun résultat'}). Saisissez latitude/longitude.")


def local_to_utc(date_str, time_str, tzname=None, utc_offset=None):
    """Convertit une date (AAAA-MM-JJ) + heure locale (HH:MM) en datetime UTC (naïf) avec le DST exact.
    -> (utc_naif, infos{tz, offset_h, abbr, avertissements})"""
    naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    warns = []
    if tzname:
        z = ZoneInfo(tzname)
        a = naive.replace(tzinfo=z, fold=0)
        b = naive.replace(tzinfo=z, fold=1)
        off_a, off_b = a.utcoffset(), b.utcoffset()
        if off_a != off_b:
            # heure ambiguë (retour à l'heure d'hiver) ou inexistante (passage à l'heure d'été)
            rt = a.astimezone(timezone.utc).astimezone(z).replace(tzinfo=None)
            if rt != naive:
                warns.append("Cette heure locale n'existe pas (passage à l'heure d'été) : l'heure a été décalée.")
            else:
                warns.append("Cette heure locale est ambiguë (changement d'heure) : première occurrence retenue (heure d'été).")
        aware = a
        off = aware.utcoffset()
        utc = aware.astimezone(timezone.utc).replace(tzinfo=None)
        return utc, dict(tz=tzname, offset_h=off.total_seconds() / 3600, abbr=aware.tzname(), avertissements=warns)
    if utc_offset is not None:
        from datetime import timedelta
        return naive - timedelta(hours=utc_offset), dict(tz=None, offset_h=utc_offset, abbr=f"UTC{utc_offset:+g}", avertissements=warns)
    raise ValueError("Fuseau ou décalage UTC requis")
