# Prototype d'implémentation de la méthode "chart for the event" (Frawley, Sports Astrology, ch.2)
import ephem, math
from datetime import datetime, timedelta
SIGNS="Ari Tau Gem Can Leo Vir Lib Sco Sag Cap Aqu Pis".split()
RULER=['Mars','Venus','Mercury','Moon','Sun','Mercury','Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']
ANTI_SIGN=lambda s:(3-s)%12   # reflexion around 0 Can/Cap: Ari->Vir(5)... computed by longitude below
def anti(l): return (180-l)%360   # miroir autour de 0 Cancer/0 Capricorne axis (90 / 270): lon' = 180 - lon
def fmt(l):
    l%=360; s=int(l//30); d=l-30*s; return f"{int(d)}°{int((d-int(d))*60):02d}' {SIGNS[s]}"
def dist(a,b): return (a-b+180)%360-180   # signed a-b
BODIES={'Sun':ephem.Sun,'Moon':ephem.Moon,'Mercury':ephem.Mercury,'Venus':ephem.Venus,'Mars':ephem.Mars,'Jupiter':ephem.Jupiter,'Saturn':ephem.Saturn,'Uranus':ephem.Uranus,'Neptune':ephem.Neptune,'Pluto':ephem.Pluto}
def lon_of(name,d):
    b=BODIES[name](); b.compute(d); return math.degrees(ephem.Ecliptic(b,epoch=d).lon)%360
def mean_node(d):
    T=(float(d)-36525.0-ephem.Date('2000/1/1 12:00')+36525.0)/36525.0
    T=(float(ephem.Date(d))-float(ephem.Date('2000/1/1 12:00')))/36525.0
    return (125.04452-1934.136261*T)%360
def true_node(d):
    T=(float(ephem.Date(d))-float(ephem.Date('2000/1/1 12:00')))/36525.0
    r=math.radians
    D=r((297.8501921+445267.1114034*T)%360); M=r((357.5291092+35999.0502909*T)%360)
    Mp=r((134.9633964+477198.8675055*T)%360); F=r((93.2720950+483202.0175233*T)%360)
    om=(125.04452-1934.136261*T)%360
    corr=(-1.4979*math.sin(2*(D-F))-0.1500*math.sin(M)-0.1226*math.sin(2*D)+0.1176*math.sin(2*F)-0.0801*math.sin(2*(Mp-F)))
    return (om+corr)%360
def chart(utc_dt,lat,lon):
    d=ephem.Date(utc_dt)
    pos={n:lon_of(n,d) for n in BODIES}
    spd={}
    for n in ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn']:
        spd[n]=dist(lon_of(n,ephem.Date(d+1/24.0)),lon_of(n,ephem.Date(d-1/24.0)))*12.0  # deg/day
    obs=ephem.Observer(); obs.lat=str(lat); obs.lon=str(lon); obs.date=d; obs.pressure=0
    ramc=float(obs.sidereal_time())  # rad
    eps=math.radians(23.4392911-0.0130042*((float(d)-36525.0-0)/36525.0)) if False else math.radians(23.4393)
    mc=math.degrees(math.atan2(math.sin(ramc),math.cos(ramc)*math.cos(eps)))%360
    phi=math.radians(lat)
    asc=math.degrees(math.atan2(math.cos(ramc),-(math.sin(ramc)*math.cos(eps)+math.tan(phi)*math.sin(eps))))%360
    # ensure ASC is in the correct half: ASC should be east of MC (0<asc-mc<180)
    if (asc-mc)%360>180: asc=(asc+180)%360
    nn=true_node(d)
    fort=(asc+pos['Moon']-pos['Sun'])%360   # formule de jour toujours
    return dict(utc=utc_dt,pos=pos,spd=spd,asc=asc,mc=mc,dsc=(asc+180)%360,ic=(mc+180)%360,nn=nn,sn=(nn+180)%360,fort=fort,lat=lat,lon=lon)
def sign_of(l): return int((l%360)//30)
def ruler_of(l): return RULER[sign_of(l)]
