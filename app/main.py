import os, threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Literal
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import geo, fixtures
from .engine.judge_fr import judge, confidence, guess_score, fmt_fr, PL_FR, SIGNS_FR, cusp_pts
from .engine.frawley_event import ruler_of, sign_of, anti
from .engine.cases import SPORT, CASES, utc as case_utc

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / 'static'
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_):
    threading.Thread(target=lambda: fixtures.get_matches(7), daemon=True).start()   # préchauffe le cache du calendrier
    yield

app = FastAPI(lifespan=lifespan, title="Astro-Foot — méthode Frawley", version="1.0",
              description="Prédiction de matchs de football selon la méthode « thème d'événement » de John Frawley (Sports Astrology). À but de divertissement / étude uniquement.")

DISCLAIMER = ("Application à but de divertissement et d'étude de la méthode décrite dans « Sports Astrology » (John Frawley). "
              "Aucune validité statistique n'est démontrée ; le livre ne donne que des anecdotes. Ne pas utiliser pour parier.")
FOOT_SPORTS = ('foot90', 'foot90et')
PROFILE_FR = {'foot90': "Football, 90 min (plage de la Lune : 5°)", 'foot90et': "Football à élimination directe, prolongation possible (plage de la Lune : 6°)",
              'usfoot': 'Football américain (test)', 'baseball': 'Baseball (test)', 'cricket1d': 'Cricket (test)',
              'crickettest': 'Cricket test (test)', 'tennis': 'Tennis (test)', 'rugby': 'Rugby (test)'}


class PredictIn(BaseModel):
    equipe_a: str = Field(..., min_length=1, description="Équipe A (en général domicile)")
    equipe_b: str = Field(..., min_length=1)
    favori: Literal['a', 'b', 'egal'] = Field(..., description="Favori selon les cotes. 'egal' = cotes égales : méthode inutilisable (Frawley p.79)")
    date: Optional[str] = Field(None, description="AAAA-MM-JJ (date locale du coup d'envoi)")
    heure: Optional[str] = Field(None, description="HH:MM (heure locale du coup d'envoi)")
    kickoff_utc: Optional[str] = Field(None, description="Alternative : coup d'envoi en UTC 'AAAA-MM-JJ HH:MM'")
    ville: Optional[str] = None
    stade: Optional[str] = None
    pays: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    fuseau: Optional[str] = Field(None, description="Fuseau IANA (ex. Europe/Paris) ; déduit des coordonnées si absent")
    utc_offset: Optional[float] = Field(None, description="Décalage UTC fixe en heures (cas historiques sans base IANA)")
    elimination: bool = Field(False, description="Match à élimination directe (prolongation possible)")
    sport: Optional[str] = Field(None, description="Réservé aux tests de validation du livre ; par défaut football")


def _place(p: PredictIn):
    warns = []
    if p.lat is not None and p.lon is not None:
        lat, lon = p.lat, p.lon
        tz = p.fuseau or (None if p.utc_offset is not None else geo.tz_for(lat, lon))
        lieu = dict(nom=', '.join(x for x in (p.stade, p.ville) if x) or f"{lat:.3f}, {lon:.3f}", source='coordonnées fournies')
    else:
        try:
            g = geo.geocode(p.stade, p.ville, p.pays)
        except LookupError as e:
            raise HTTPException(422, str(e))
        lat, lon, tz = g['lat'], g['lon'], p.fuseau or g['tz']
        lieu = dict(nom=g['nom'], source=g['source'])
    if abs(lat) > 66:
        raise HTTPException(422, "Latitude trop élevée (>66°) : thème non défini (le livre ne traite pas ce cas).")
    lieu.update(lat=round(lat, 4), lon=round(lon, 4))
    return lat, lon, tz, lieu, warns


def _house_info(ch, L, names):
    c = cusp_pts(ch)
    out = {}
    for h, side in ((1, 'F'), (10, 'F'), (7, 'D'), (4, 'D')):
        s = sign_of(c[h])
        out[str(h)] = dict(equipe=names[side], role='favori' if side == 'F' else 'outsider', pointe=fmt_fr(c[h]), lon=round(c[h], 3),
                           signe=SIGNS_FR[s], seigneur_signe=PL_FR[ruler_of(c[h])], seigneur_retenu=PL_FR[L[h]] if L[h] else None)
    return out


@app.post('/api/predict')
def predict(p: PredictIn):
    if p.sport and p.sport not in SPORT:
        raise HTTPException(422, f"sport inconnu : {p.sport}")
    sport = p.sport or ('foot90et' if p.elimination else 'foot90')
    lat, lon, tz, lieu, warns = _place(p)
    # --- heure
    if p.kickoff_utc:
        try:
            utc_dt = datetime.strptime(p.kickoff_utc[:16].replace('T', ' '), "%Y-%m-%d %H:%M")
        except ValueError:
            raise HTTPException(422, "kickoff_utc invalide (attendu AAAA-MM-JJ HH:MM)")
        if tz:
            loc = utc_dt.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(tz))
            tzinfo = dict(tz=tz, offset_h=loc.utcoffset().total_seconds() / 3600, abbr=loc.tzname(), avertissements=[])
            local_dt = loc.replace(tzinfo=None)
        else:
            raise HTTPException(422, "fuseau introuvable pour ce lieu")
    else:
        if not (p.date and p.heure):
            raise HTTPException(422, "date et heure locales requises (ou kickoff_utc)")
        try:
            utc_dt, tzinfo = geo.local_to_utc(p.date, p.heure, tz, p.utc_offset)
            local_dt = datetime.strptime(f"{p.date} {p.heure}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            raise HTTPException(422, f"date/heure invalide : {e}")
    warns += tzinfo['avertissements']
    if utc_dt.year < 1850 or utc_dt.year > 2100:
        raise HTTPException(422, "date hors de la plage supportée (1850-2100)")
    fav_side = {'a': 'F', 'b': 'F'}.get(p.favori)
    names_ab = {'a': p.equipe_a, 'b': p.equipe_b}
    fav_name = names_ab.get(p.favori, p.equipe_a)
    dog_name = p.equipe_b if p.favori in ('a', 'egal') else p.equipe_a
    names = {'F': fav_name, 'D': dog_name}
    j = judge(utc_dt, lat, lon, sport, names)
    ch = j['chart']
    to_side = lambda s: ('a' if (s == 'F') == (p.favori in ('a', 'egal')) else 'b')   # camp F/D -> équipe a/b
    # --- avertissements de pertinence (Frawley p.92-93, spec §1.1 / §5.9)
    if sport not in FOOT_SPORTS:
        warns.append("Sport hors football : mode test de validation du livre uniquement.")
    if local_dt.weekday() == 5 and 13 <= local_dt.hour + local_dt.minute / 60 <= 16:
        warns.append("Samedi vers 15 h : beaucoup de matchs partent à la même heure ; Frawley juge la méthode peu fiable dans ce cas.")
    if local_dt.hour >= 0 and local_dt.hour < 6:
        warns.append("Heure locale très tardive/matinale : vérifier le coup d'envoi.")
    if utc_dt < datetime.now(timezone.utc).replace(tzinfo=None):
        warns.append("Match déjà passé : lecture à titre d'étude.")
    for h in (1, 7):
        if ruler_of(ch['asc'] if h == 1 else ch['dsc']) == 'Moon':
            warns.append("La Lune gouverne l'Ascendant/le Descendant (Cancer) : cas délicat, confiance réduite (spec §4.2).")
            break
    if j['stymied']:
        warns.append("La Lune est seigneur d'une maison et son dispositeur est inutilisable : les aspects de la Lune ne comptent pas (cas « stymied »).")
    # --- décision
    method_unusable = p.favori == 'egal'
    T = j['testimonies']
    if method_unusable:
        res, vainqueur, conf = 'indetermine', None, 'aucune'
        raison = ("Les deux équipes sont à égalité (cotes égales) : « We can't use this method » (Frawley, p.79). "
                  "Le thème ne dit pas qui est favori ; sans favori, impossible d'attribuer les maisons 1/10 et 7/4.")
        score = None
        T_out = []
    else:
        conf = confidence(j)
        if j['draw']:
            res, vainqueur = 'nul', None
            raison = "Les témoignages des deux camps se compensent et aucun témoignage fort n'apparaît : match nul possible (hypothèse non issue du livre)."
        else:
            res = to_side(j['result'])
            vainqueur = names['F'] if j['result'] == 'F' else names['D']
            if j['decided_tier'] is None:
                raison = ("Aucun témoignage ne départage nettement : règle par défaut de Frawley, « les favoris gagnent s'il n'y a pas de preuve du contraire » (p.114). "
                          f"Victoire de {vainqueur} avec une confiance faible.")
            else:
                lv = {1: "placements des seigneurs/Lune/Fortuna sur les pointes", 2: "aspect final de la Lune et témoignages secondaires", 3: "témoignages d'appoint"}[j['decided_tier']]
                raison = (f"Le niveau {j['decided_tier']} ({lv}) départage les camps avec un écart de {j['margin']:.1f} points en faveur de {vainqueur}. "
                          "Les témoignages sont comparés par niveaux de force décroissante (hypothèse d'implémentation, le livre ne donne aucune formule).")
        gf, gd, txt, note = guess_score(j)
        ga, gb = (gf, gd) if p.favori in ('a', 'egal') else (gd, gf)
        score = dict(a=ga, b=gb, texte=f"{p.equipe_a} {ga}–{gb} {p.equipe_b}", note=note,
                     avertissement="Score purement indicatif : Frawley lui-même parle de « educated guess » (p.91) ; heuristique ajustée sur très peu d'exemples.")
        T_out = []
    for i, t in enumerate(sorted(T, key=lambda t: (t['tier'], -t['w']))):
        if method_unusable:
            break
        T_out.append(dict(n=i + 1, equipe=to_side(t['side']), equipe_nom=names[t['side']], camp='favori' if t['side'] == 'F' else 'outsider',
                          poids=t['w'], niveau=t['tier'], force='forte' if t['w'] >= 7 else ('moyenne' if t['w'] >= 3.5 else 'faible'),
                          categorie=t['cat'], texte=t['text'], source_livre=t['ref'], decisif=t['decisif']))
    pos = ch['pos']
    planets = []
    for n in ('Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'):
        planets.append(dict(id=n, nom=PL_FR[n], lon=round(pos[n], 3), pos=fmt_fr(pos[n]),
                            retro=(ch['spd'][n] < 0) if n in ch['spd'] else None))
    cu = cusp_pts(ch)
    theme = dict(
        asc=dict(lon=round(ch['asc'], 3), pos=fmt_fr(ch['asc']), seigneur=PL_FR[ruler_of(ch['asc'])]),
        mc=dict(lon=round(ch['mc'], 3), pos=fmt_fr(ch['mc']), seigneur=PL_FR[ruler_of(ch['mc'])]),
        dsc=dict(lon=round(ch['dsc'], 3), pos=fmt_fr(ch['dsc']), seigneur=PL_FR[ruler_of(ch['dsc'])]),
        ic=dict(lon=round(ch['ic'], 3), pos=fmt_fr(ch['ic']), seigneur=PL_FR[ruler_of(ch['ic'])]),
        lune=dict(lon=round(pos['Moon'], 3), pos=fmt_fr(pos['Moon']), reste_dans_le_signe=round(30 - pos['Moon'] % 30, 2), plage_degres=round(j['moon_range'], 2)),
        fortuna=dict(lon=round(j['fort'], 3), pos=fmt_fr(j['fort']), antiscion=fmt_fr(j['fort_anti']), antiscion_lon=round(j['fort_anti'], 3),
                     dispositeur=PL_FR[j['dispositor']], formule="ASC + Lune − Soleil (formule de jour, jamais inversée la nuit : Frawley p.84)"),
        noeud_nord=dict(lon=round(ch['nn'], 3), pos=fmt_fr(ch['nn'])), noeud_sud=dict(lon=round(ch['sn'], 3), pos=fmt_fr(ch['sn'])),
        planetes=planets, maisons=_house_info(ch, j['lords'], names),
        seigneurs={str(h): (PL_FR[pl] if pl else None) for h, pl in j['lords'].items()},
        notes_seigneurs=j['lord_notes'],
        systeme="Maisons Placidus ; seules les pointes 1/4/7/10 (ASC, IC, DSC, MC) servent à la méthode.")
    out = dict(
        match=dict(equipe_a=p.equipe_a, equipe_b=p.equipe_b, favori=p.favori, favori_nom=fav_name if p.favori != 'egal' else None,
                   outsider_nom=dog_name if p.favori != 'egal' else None, profil=sport, profil_libelle=PROFILE_FR.get(sport, sport),
                   coup_denvoi_local=local_dt.strftime('%Y-%m-%d %H:%M'), coup_denvoi_utc=utc_dt.strftime('%Y-%m-%d %H:%M'),
                   fuseau=tzinfo['tz'], decalage_utc_h=tzinfo['offset_h'], abbr_fuseau=tzinfo['abbr'], lieu=lieu),
        theme=theme,
        prediction=dict(resultat=res, vainqueur=vainqueur, score=score, confiance=conf, niveau_decisif=j['decided_tier'] if not method_unusable else None,
                        points_favori=round(j['sumF'], 1) if not method_unusable else None, points_outsider=round(j['sumD'], 1) if not method_unusable else None,
                        raisonnement=raison, methode_utilisable=not method_unusable),
        temoignages=T_out,
        sequence_lune=j['moon_seq'] if not method_unusable else [],
        avertissements=warns,
        mentions=DISCLAIMER)
    # noms d'équipes dans la séquence de la Lune : nom_camp = nom, ajout 'equipe' a/b
    for s in out['sequence_lune']:
        s['equipe'] = to_side(s['camp'])
    return out


@app.get('/api/matches')
def matches(days: int = Query(7, ge=1, le=14), refresh: bool = False):
    return fixtures.get_matches(days, force=refresh)


@app.get('/api/geocode')
def geocode(q: str = Query(..., min_length=2), ville: Optional[str] = None):
    try:
        g = geo.geocode(q, ville)
    except LookupError as e:
        raise HTTPException(404, str(e))
    return g


@app.get('/api/cases')
def cases_list():
    return [dict(id=c['id'], nom=c['name'], sport=c['sport'], date_locale=c['dt'], decalage_utc=c['tz'], lat=c['lat'], lon=c['lon'],
                 favori_gagne=c['fav_wins'], resultat_livre=c['score'], ref=c['src']) for c in CASES]


@app.get('/api/status')
def status():
    return dict(ok=True, football_data_key=bool(os.environ.get('FOOTBALL_DATA_API_KEY')), nominatim=geo.NOMINATIM)


@app.get('/')
def index():
    return FileResponse(STATIC / 'index.html')


app.mount('/static', StaticFiles(directory=STATIC), name='static')


