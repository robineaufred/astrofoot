"""Moteur de jugement (méthode « thème d'événement » de Frawley, Sports Astrology ch.2).

Dérivé de /workspace/frawley/judge.py : la LOGIQUE et les POIDS sont identiques (ils ont été
réglés sur les 25 thèmes du livre : ce sont des hypothèses [HYP], pas des règles du livre).
Différences : sortie structurée, explications en français, pas de print.
"""
import ephem
from .frawley_event import chart, anti, dist, ruler_of, sign_of, fmt as _fmt_en, SIGNS
from .cases import SPORT

ASP = {'conj': 0, 'sext': 60, 'sq': 90, 'tri': 120, 'opp': 180}
ASP_FR = {'conj': 'conjonction', 'sext': 'sextile', 'sq': 'carré', 'tri': 'trigone', 'opp': 'opposition'}
PL7 = ['Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']
PL_FR = {'Sun': 'Soleil', 'Moon': 'Lune', 'Mercury': 'Mercure', 'Venus': 'Vénus', 'Mars': 'Mars',
         'Jupiter': 'Jupiter', 'Saturn': 'Saturne', 'Uranus': 'Uranus', 'Neptune': 'Neptune', 'Pluto': 'Pluton'}
SIGNS_FR = ['Bélier', 'Taureau', 'Gémeaux', 'Cancer', 'Lion', 'Vierge', 'Balance', 'Scorpion',
            'Sagittaire', 'Capricorne', 'Verseau', 'Poissons']
REF = {'cusp': "Frawley, p.81-82", 'fort': "Frawley, p.84 (« antiscion de Fortuna, pas le corps »)",
       'moon': "Frawley, p.83-88", 'node': "Frawley, p.89-90", 'comb': "Frawley, p.90 (combustion à 2°)",
       'pluto': "Frawley, p.90", 'uranus': "Frawley, p.90", 'fortasp': "Frawley, p.88-89"}


def fmt_fr(l):
    l %= 360
    s = int(l // 30)
    d = l - 30 * s
    return f"{int(d)}°{int((d - int(d)) * 60):02d}′ {SIGNS_FR[s]}"


def cusp_pts(ch):
    return {1: ch['asc'], 10: ch['mc'], 7: ch['dsc'], 4: ch['ic']}


def team_of_house(h):
    return 'F' if h in (1, 10) else 'D'


def resolve_lords(ch):
    c = cusp_pts(ch)
    L = {h: ruler_of(c[h]) for h in (1, 7, 10, 4)}
    notes = []
    moon = ch['pos']['Moon']
    stymied = False
    for h in (1, 7):
        if L[h] == 'Moon':
            disp = ruler_of(moon)
            other = L[7 if h == 1 else 1]
            if disp == 'Moon' or disp == other:
                notes.append(f"Seigneur {h} = Lune ; son dispositeur ({PL_FR[disp]}) est inutilisable → pas de seigneur {h} et les aspects de la Lune sont désactivés (cas « stymied » du livre, p.102).")
                L[h] = None
                stymied = True
            else:
                notes.append(f"Seigneur {h} = Lune → remplacée par son dispositeur {PL_FR[disp]} (la Lune reste le « flux des événements », p.88).")
                L[h] = disp
    for h in (10, 4):
        if L[h] == 'Moon':
            notes.append(f"Seigneur {h} = Lune → pas de seigneur {h} (la Lune reste le flux, p.88).")
            L[h] = None
    for h in (10, 4):
        if L[h] is not None and L[h] in (L[1], L[7]):
            if (h == 10 and L[h] == L[1]) or (h == 4 and L[h] == L[7]):
                notes.append(f"Seigneur {h} ({PL_FR[L[h]]}) = doublon du seigneur {1 if h == 10 else 7} → abandonné (priorité aux seigneurs 1 et 7, p.88-89).")
            else:
                notes.append(f"Seigneur {h} ({PL_FR[L[h]]}) est déjà seigneur 1/7 du camp adverse → abandonné (priorité 1/7, p.88-89).")
            L[h] = None
    return L, notes, stymied


def aspect_event(name, target_lon, angle, d0, lon_of, maxorb=5.0, maxdays=60, step=0.5):
    """La planète 'name' va-t-elle former l'aspect 'angle' au point fixe target_lon, en s'appliquant,
    sans station ni aspect préalable (prohibition) ? -> (ok, raison)"""
    d = ephem.Date(d0)
    p0 = lon_of(name, d)
    for sgn in ([1] if angle in (0, 180) else [1, -1]):
        tgt = (target_lon + sgn * angle) % 360
        gap = dist(tgt, p0)
        if abs(gap) > maxorb:
            continue
        p1 = lon_of(name, ephem.Date(d + 0.1))
        v = dist(p1, p0) / 0.1
        if v == 0 or (gap > 0) != (v > 0):
            continue
        prev = p0
        t = 0
        prohibit = None
        others = [o for o in PL7 if o != name]
        oprev = {o: lon_of(o, d) for o in others}
        while t < maxdays:
            t += step
            pn = lon_of(name, ephem.Date(d + t))
            if (dist(pn, prev) > 0) != (v > 0) and abs(dist(pn, prev)) > 0:
                return (False, 'station avant perfection')
            if (dist(tgt, prev) > 0) != (dist(tgt, pn) > 0) and abs(dist(tgt, pn)) < 20:
                if prohibit:
                    return (False, f'prohibition par {prohibit}')
                return (True, f'se perfectionne dans ~{t:.1f} jour(s)')
            for o in others:
                on = lon_of(o, ephem.Date(d + t))
                for a in (0, 60, 90, 120, 180):
                    for s2 in ((1,) if a in (0, 180) else (1, -1)):
                        r0 = dist(prev, (oprev[o] + s2 * a) % 360)
                        r1 = dist(pn, (on + s2 * a) % 360)
                        if r0 * r1 < 0 and abs(r1) < 10 and not prohibit:
                            prohibit = o
            prev = pn
            oprev = {o: lon_of(o, ephem.Date(d + t)) for o in others}
            if abs(dist(tgt, pn)) > abs(gap) + 1:
                break
        return (False, 'non atteint')
    return (False, 'pas applicant / hors orbe')


DEFAULT_W = dict(L17_enemy=10, L410_enemy=6, L17_own=4, L410_own=3, moon_cusp=7, moon_anti_cusp=5,
                 fort_anti_cusp=9, node17=8, node410=5, fortnode=6, comb17=7, comb410=4, moon_final=6,
                 fort_asp_L17=5, fort_asp_L410=2, disp=3, pluto=8, uranus=3)


def judge(utc_dt, lat, lon, sport, names=None, lon_of=None):
    """Retourne un dict structuré. names={'F': nom du favori, 'D': nom de l'outsider}."""
    from .frawley_event import lon_of as _lon_of
    lon_of = lon_of or _lon_of
    names = names or {'F': 'le favori', 'D': "l'outsider"}
    W = DEFAULT_W
    ORB = 3.3
    ch = chart(utc_dt, lat, lon)
    sp = SPORT[sport]
    d0 = ephem.Date(utc_dt)
    pos = ch['pos']
    cu = cusp_pts(ch)
    L, lord_notes, stym = resolve_lords(ch)
    T = []
    team = {1: 'F', 10: 'F', 7: 'D', 4: 'D'}
    other = lambda s: 'D' if s == 'F' else 'F'
    nm = lambda s: names[s]
    F = ch['fort']
    Fa = anti(F)
    near = lambda a, b: abs(dist(a, b))

    def add(side, w, text, tier, cat, ref):
        T.append(dict(side=side, w=round(w, 1), tier=tier, cat=cat, text=text, ref=ref))

    def lord_lbl(h, pl):
        return f"Seigneur {h} ({PL_FR[pl]}), significateur de {nm(team[h])}"

    # A. placement des seigneurs (corps et antiscion) près des pointes
    for h, pl in L.items():
        if pl is None:
            continue
        for kind, lo, fac in (('corps', pos[pl], 1.0), ('antiscion', anti(pos[pl]), 0.8)):
            for H, cl in cu.items():
                dd = dist(lo, cl)
                if -ORB <= dd < 0:
                    rel = 'on'
                elif 0 <= dd <= ORB:
                    rel = 'in'
                else:
                    continue
                clos = 1 - abs(dd) / (ORB + 0.5)
                enemy = (team[h] != team_of_house(H))
                what = f"{'son antiscion (' + fmt_fr(lo) + ')' if kind == 'antiscion' else PL_FR[pl] + ' (' + fmt_fr(lo) + ')'}"
                where = (f"à {abs(dd):.1f}° AVANT la pointe de la maison {H} ({fmt_fr(cl)}) : il est « sur la pointe »"
                         if rel == 'on' else
                         f"à {abs(dd):.1f}° APRÈS la pointe de la maison {H} ({fmt_fr(cl)}) : il est « juste dedans »")
                if enemy:
                    w = (W['L17_enemy'] if h in (1, 7) else W['L410_enemy']) * fac * clos
                    side = team[h] if rel == 'on' else other(team[h])
                    if rel == 'on':
                        why = (f"Une planète sur la pointe d'une maison adverse la contrôle : {nm(team[h])} prend le dessus. "
                               "(« A planet on a cusp controls that house »)")
                    else:
                        why = (f"Un seigneur juste dedans une maison adverse est contrôlé par elle (« en prison ») : {nm(team[h])} est affaibli → avantage {nm(side)}.")
                else:
                    w = (W['L17_own'] if h in (1, 7) else W['L410_own']) * fac * clos
                    side = team[h]
                    why = f"Placement dans sa propre maison : renforce {nm(side)} (témoignage plus faible que dans une maison adverse)."
                add(side, w, f"{lord_lbl(h, pl)} : {what} {where}. {why}", 1 if h in (1, 7) else 2, 'placement', REF['cusp'])
    # Lune près des pointes
    for kind, lo, fac in (('corps', pos['Moon'], W['moon_cusp']), ('antiscion', anti(pos['Moon']), W['moon_anti_cusp'])):
        for H, cl in cu.items():
            dd = dist(lo, cl)
            if -ORB <= dd <= ORB:
                clos = 1 - abs(dd) / (ORB + 0.5)
                s = team_of_house(H)
                what = 'La Lune' if kind == 'corps' else "L'antiscion de la Lune"
                add(s, fac * clos, f"{what} ({fmt_fr(lo)}) est à {abs(dd):.1f}° de la pointe de la maison {H} ({fmt_fr(cl)}), maison de {nm(s)} → favorise {nm(s)}.", 1, 'lune_pointe', REF['moon'])
    # antiscion de Fortuna sur les pointes
    for H, cl in cu.items():
        dd = dist(Fa, cl)
        if abs(dd) <= ORB:
            s = team_of_house(H)
            add(s, W['fort_anti_cusp'] * (1 - abs(dd) / (ORB + 0.5)),
                f"L'antiscion de la Part de Fortune ({fmt_fr(Fa)}) est à {abs(dd):.1f}° de la pointe de la maison {H} ({fmt_fr(cl)}) → favorise {nm(s)}. Frawley : « l'un des témoignages les plus puissants, peut-être le plus puissant de tous ».",
                1, 'fortuna_antiscion', REF['fort'])
    # B. Nœuds, combustion
    for h, pl in L.items():
        if pl is None:
            continue
        for kind, lo, fac in (('corps', pos[pl], 1.0), ('antiscion', anti(pos[pl]), 0.8)):
            for nname, nl, nside in (('Nœud Nord', ch['nn'], team[h]), ('Nœud Sud', ch['sn'], other(team[h]))):
                dd = near(lo, nl)
                if dd <= (2.0 if kind == 'corps' else 1.0):
                    w = (W['node17'] if h in (1, 7) else W['node410']) * fac * (1 - dd / 2.5)
                    eff = 'renforcé (« North Node good »)' if 'Nord' in nname else 'affaibli (« South Node bad »)'
                    sub = PL_FR[pl] if kind == 'corps' else f"l'antiscion de {PL_FR[pl]}"
                    add(nside, w, f"{lord_lbl(h, pl)} : {sub} est conjoint au {nname} (à {dd:.1f}°) → {nm(team[h])} est {eff}, ce qui favorise {nm(nside)}.", 1 if h in (1, 7) else 2, 'noeud', REF['node'])
        if pl != 'Sun' and near(pos[pl], pos['Sun']) <= 2.0:
            s = other(team[h])
            add(s, W['comb17'] if h in (1, 7) else W['comb410'],
                f"{lord_lbl(h, pl)} est combuste (à {near(pos[pl], pos['Sun']):.1f}° du Soleil, limite 2°) → {nm(team[h])} est affaibli, favorise {nm(s)}.",
                1 if h in (1, 7) else 2, 'combustion', REF['comb'])
    if near(F, ch['nn']) <= 2.0:
        add('F', W['fortnode'], f"La Part de Fortune ({fmt_fr(F)}) est sur le Nœud Nord (Fortuna « appartient » au favori) → favorise {nm('F')}.", 2, 'fortuna_noeud', REF['node'])
    if near(F, ch['sn']) <= 2.0:
        add('D', W['fortnode'], f"La Part de Fortune ({fmt_fr(F)}) est sur le Nœud Sud → défavorable au favori, favorise {nm('D')}.", 2, 'fortuna_noeud', REF['node'])
    if near(F, pos['Sun']) <= 2.0:
        add('D', 3, f"La Part de Fortune est combuste (à moins de 2° du Soleil) : « bonne nouvelle pour les outsiders » → favorise {nm('D')}.", 3, 'fortuna_combuste', REF['comb'])
    # C. Lune : balayage d'aspects
    m0 = pos['Moon']
    to_end = 30 - (m0 % 30)
    R = sp['range']
    if R is None:
        R = to_end + (30 if to_end <= 2.0 else 0)
    R = min(R, to_end) if sp['range'] is not None else R
    targets = []
    for h, pl in L.items():
        if pl is None:
            continue
        targets.append((f"seigneur {h} ({PL_FR[pl]}, {nm(team[h])})", pos[pl], team[h], 'body', h))
        targets.append((f"antiscion du seigneur {h} ({PL_FR[pl]}, {nm(team[h])})", anti(pos[pl]), team[h], 'anti', h))
    targets.append(("Part de Fortune", F, 'FORT', 'body', 0))
    targets.append(("antiscion de la Part de Fortune", Fa, 'FORT', 'anti', 0))
    evs = []
    for tn, tl, tm, kind, h in targets:
        for an, ang in ASP.items():
            for sg in ((1,) if ang in (0, 180) else (1, -1)):
                trav = (((tl + sg * ang) % 360) - m0) % 360
                if 0.001 < trav <= R:
                    evs.append((trav, tn, an, tm, kind))
    if stym:
        evs = []
    evs.sort()
    if sp['et'] and not [e for e in evs if e[0] <= R] and not stym:
        for tn, tl, tm, kind, h in targets:
            for an, ang in ASP.items():
                for sg in ((1,) if ang in (0, 180) else (1, -1)):
                    trav = (((tl + sg * ang) % 360) - m0) % 360
                    if R < trav <= R + 1.1 and tm == 'FORT':
                        evs.append((trav, tn, an, tm, kind))
        evs.sort()
    SHORT = (sp['range'] is not None and sp['range'] <= 8)
    final = None
    seq = []
    for trav, tn, an, tm, kind in evs:
        side = ('F' if an in ('conj', 'tri', 'sext') else 'D') if tm == 'FORT' else tm
        final = (trav, tn, an, side, kind, tm)
        seq.append(dict(distance=round(trav, 1), cible=tn, aspect=ASP_FR[an], camp=side, nom_camp=nm(side), final=False))
        if tm == 'FORT' and SHORT:
            break
        if an == 'conj' and kind == 'body':
            break
        if an == 'conj' and kind == 'anti' and trav > 6.0:
            break
    if final:
        seq[-1]['final'] = True
        wm = W['moon_final'] * (1.0 if (final[4] == 'body' or final[1].endswith('Fortune')) else (0.9 if final[2] in ('conj', 'opp') else 0.5))
        fs = final[3]
        if final[5] == 'FORT':
            why = f"Aspect à Fortuna ou à son antiscion : conjonction/sextile/trigone → favori, carré/opposition → outsider ; « les aspects à Fortuna sont finals » (p.88)."
        else:
            why = "La nature de l'aspect importe peu : un aspect au seigneur d'une équipe désigne cette équipe."
        late = " (au-delà de la plage « règlementaire » : possible prolongation)" if final[0] > R else ""
        add(fs, wm, f"Aspect FINAL de la Lune : {ASP_FR[final[2]]} {('au ' if not final[1].startswith(('antiscion', 'Part')) else 'à l’')}{final[1]} après {final[0]:.1f}° de course (plage {R:g}°){late} → {nm(fs)}. « Moon's final aspect wins ». {why}",
            2, 'lune_aspect_final', REF['moon'])
    # D. aspects planète -> Fortuna
    dispo = ruler_of(F)
    for h, pl in L.items():
        if pl is None:
            continue
        wgt = W['fort_asp_L17'] if h in (1, 7) else W['fort_asp_L410']
        for tn, tl in (('Fortuna', F), ("l'antiscion de Fortuna", Fa)):
            for an in ('conj', 'opp'):
                ok, why = aspect_event(pl, tl, ASP[an], d0, lon_of)
                if ok:
                    if team[h] == 'F':
                        side = 'F' if an == 'conj' else 'D'
                    elif an == 'conj':
                        side = 'D'
                    else:
                        side = 'D' if tn == 'Fortuna' else 'F'
                    add(side, wgt, f"{lord_lbl(h, pl)} applique une {ASP_FR[an]} à {tn} ({why}) → favorise {nm(side)}.", 2 if h in (1, 7) else 3, 'aspect_fortuna', REF['fortasp'])
    if dispo != 'Moon' and dispo not in (L[1], L[7]):
        for tn, tl in (('Fortuna', F), ("l'antiscion de Fortuna", Fa)):
            for an in ('conj', 'opp'):
                ok, why = aspect_event(dispo, tl, ASP[an], d0, lon_of)
                if ok:
                    s = 'F' if an == 'conj' else 'D'
                    add(s, W['disp'], f"Le dispositeur de Fortuna ({PL_FR[dispo]}) applique une {ASP_FR[an]} à {tn} ({why}) → favorise {nm(s)}.", 2, 'dispositeur', REF['fortasp'])
    # E. Pluton / Uranus
    pl_ = pos['Pluto']
    for H in (1, 10):
        dd = dist(pl_, cu[H])
        if -2.0 <= dd <= 2.0:
            add('D', W['pluto'], f"Pluton ({fmt_fr(pl_)}) est à {abs(dd):.1f}° de la pointe de la maison {H} : effet destructeur sur le favori (« Pluto has a powerful destructive effect if placed directly on a relevant cusp ») → favorise {nm('D')}.", 1, 'pluton', REF['pluto'])
    for tn, tl in (('Fortuna', F), ("l'antiscion de Fortuna", Fa), ('le dispositeur de Fortuna', pos[dispo] if dispo in pos else -999)):
        if near(pl_, tl) <= 1.0 or near(pl_, (tl + 180) % 360) <= 1.0:
            add('D', W['pluto'], f"Pluton est en conjonction/opposition à {tn} (≤1°) : Pluton « en veut aux favoris » → favorise {nm('D')}.", 3, 'pluton', REF['pluto'])
    ur = pos['Uranus']
    if -1.5 <= dist(ur, cu[10]) < 0:
        add('F', W['uranus'], f"Uranus s'applique tout près de la pointe du Milieu du Ciel (≤1,5°) → favorise {nm('F')} (témoignage jugé peu constant par l'auteur).", 2, 'uranus', REF['uranus'])

    # Décision (hiérarchie par niveaux, [HYP])
    tsum = lambda side, tier: sum(t['w'] for t in T if t['side'] == side and t['tier'] == tier)
    res = 'F'
    decided_tier = None
    margin = 0.0
    for tier in (1, 2, 3):
        a, b = tsum('F', tier), tsum('D', tier)
        if abs(a - b) >= 1.0:
            res = 'F' if a > b else 'D'
            decided_tier = tier
            margin = abs(a - b)
            break
    draw = False
    if decided_tier is None and sp['draw'] and not any(t['tier'] == 1 for t in T) and \
            any(t['side'] == 'F' for t in T) and any(t['side'] == 'D' for t in T):
        draw = True   # [HYP] non testé sur le livre : témoignages qui se compensent, match nul possible
    # marquer les témoignages décisifs : ceux du niveau décisif en faveur du vainqueur
    for t in T:
        t['decisif'] = (decided_tier is not None and t['tier'] == decided_tier and t['side'] == res)
    sF = sum(t['w'] for t in T if t['side'] == 'F')
    sD = sum(t['w'] for t in T if t['side'] == 'D')
    return dict(chart=ch, lords=L, lord_notes=lord_notes, stymied=stym, testimonies=T, result=res, draw=draw,
                decided_tier=decided_tier, margin=margin, sumF=sF, sumD=sD, moon_seq=seq, moon_range=R,
                moon_final_dist=(final[0] if final else None), sport=sport, sport_profile=sp,
                lord_planets=L, fort=F, fort_anti=Fa, dispositor=dispo)


def confidence(j):
    if j['draw']:
        return 'faible'
    if j['decided_tier'] is None:
        return 'faible'
    if j['decided_tier'] == 1 and j['margin'] >= 5:
        return 'élevée'
    if j['decided_tier'] in (1, 2):
        return 'moyenne'
    return 'faible'


def guess_score(j):
    """Score indicatif [HYP] (§4.9 de la spec) : « educated guess » selon Frawley (p.91). Retourne (buts_fav, buts_out, texte, note)."""
    T = j['testimonies']
    cnt = lambda side: len([1 for t in T if t['side'] == side and t['tier'] <= 2 and t['w'] >= 2])
    nF, nD = cnt('F'), cnt('D')
    if j['draw']:
        g = 0 if (nF + nD) == 0 else 1
        return g, g, f"{g}-{g}", "Témoignages qui se compensent : nul."
    win = j['result']
    nw, nl = (nF, nD) if win == 'F' else (nD, nF)
    loser = 1 if nl >= 1 else 0
    # [HYP] a priori simple : le gagnant marque 2 buts (1 seul s'il n'y a aucune preuve : victoire « par défaut »),
    # le perdant 1 s'il a au moins un témoignage, sinon 0 (« no testimony => unlikely to score », p.91).
    winner = 1 if j['decided_tier'] is None else 2
    winner = max(winner, loser + 1)
    gf, gd = (winner, loser) if win == 'F' else (loser, winner)
    note = ""
    if j['sport_profile']['et'] and j['moon_final_dist'] is not None and j['moon_final_dist'] > j['sport_profile']['range']:
        note = "Le dernier aspect de la Lune tombe au-delà de la plage normale : l'issue pourrait se jouer en prolongation."
    return gf, gd, f"{gf}-{gd}", note
