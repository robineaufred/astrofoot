from datetime import datetime, timedelta
# name, local datetime, utc offset hours, lat, lon, favourite, underdog, sport, fav_wins (True/False), book note
# sport params: moon_range (deg), et (extra time possible), draw (draw possible)
CASES=[
 dict(id="E01",name="Juventus (fav) v Dortmund — CL final",dt="1997-05-28 20:30",tz=2,lat=48.137,lon=11.575,sport="foot90et",fav_wins=False,score="Dortmund 3-1",src="p.94",known=dict(asc="2Sag34",mc="24Vir59")),
 dict(id="E02",name="Scotland (fav) v Wales — Kilmarnock",dt="1997-05-27 20:00",tz=1,lat=55.61,lon=-4.50,sport="foot90",fav_wins=False,score="Wales 1-0",src="p.96"),
 dict(id="E03",name="Marseille (fav) v Red Star — EC final, Bari",dt="1991-05-29 20:45",tz=2,lat=41.117,lon=16.87,sport="foot90et",fav_wins=False,score="0-0, Red Star on penalties",src="p.97",known=dict(asc="14Sag54",mc="5Lib21")),
 dict(id="E04",name="Arsenal (fav) v Swindon — League Cup final 1969",dt="1969-03-15 15:00",tz=1,lat=51.556,lon=-0.28,sport="foot90et",fav_wins=False,score="Swindon 3-1 a.e.t.",src="p.98"),
 dict(id="E05",name="Super Bowl XLI Colts (fav) v Bears",dt="2007-02-04 18:25",tz=-5,lat=25.958,lon=-80.239,sport="usfoot",fav_wins=True,score="Colts 29-17",src="p.99"),
 dict(id="E06",name="Kansas City (fav) v Pittsburgh",dt="1998-10-26 19:20",tz=-6,lat=39.10,lon=-94.58,sport="usfoot",fav_wins=False,score="Pittsburgh won",src="p.101"),
 dict(id="E07",name="World Series 1919 g.1 White Sox (fav) v Reds",dt="1919-10-01 15:00",tz=-5,lat=39.10,lon=-84.51,sport="baseball",fav_wins=False,score="Cincinnati won",src="p.102"),
 dict(id="E08",name="Super Bowl XXXIV Rams (fav) v Titans",dt="2000-01-30 18:26",tz=-5,lat=33.749,lon=-84.388,sport="usfoot",fav_wins=True,score="Rams 23-16",src="p.103"),
 dict(id="E09",name="Super Bowl XXXVIII Patriots (fav) v Panthers",dt="2004-02-01 17:25",tz=-6,lat=29.76,lon=-95.37,sport="usfoot",fav_wins=True,score="Patriots 32-29",src="p.105"),
 dict(id="E10",name="Super Bowl XXXVI Rams (fav) v Patriots",dt="2002-02-03 17:20",tz=-6,lat=29.95,lon=-90.07,sport="usfoot",fav_wins=False,score="Patriots 20-17",src="p.106"),
 dict(id="E11",name="NatWest SF Lancashire (fav) v Yorkshire, Manchester",dt="1996-08-13 10:30",tz=1,lat=53.48,lon=-2.24,sport="cricket1d",fav_wins=True,score="Lancashire won",src="p.108"),
 dict(id="E12",name="NatWest SF Surrey (fav) v Essex, London",dt="1996-08-13 10:30",tz=1,lat=51.51,lon=-0.13,sport="cricket1d",fav_wins=False,score="Essex won",src="p.108"),
 dict(id="E13",name="French Open final 2007 Nadal (fav) v Federer",dt="2007-06-10 15:09",tz=2,lat=48.85,lon=2.25,sport="tennis",fav_wins=True,score="Nadal 6-3 4-6 6-3 6-4",src="p.109"),
 dict(id="E14",name="Test match 1882 England (fav) v Australia, The Oval",dt="1882-08-28 12:10",tz=0,lat=51.51,lon=-0.13,sport="crickettest",fav_wins=False,score="Australia won by 7 runs",src="p.111"),
 dict(id="E15",name="Ashes 2006 Perth Australia (fav) v England",dt="2006-12-14 10:30",tz=8,lat=-31.95,lon=115.86,sport="crickettest",fav_wins=True,score="Australia won",src="p.112-113"),
 dict(id="E16",name="Ashes 2007 Sydney Australia (fav) v England",dt="2007-01-02 10:30",tz=11,lat=-33.87,lon=151.21,sport="crickettest",fav_wins=True,score="Australia won",src="p.113"),
 dict(id="E17",name="Rugby Bath (fav) v Newcastle",dt="1997-08-23 14:15",tz=1,lat=51.38,lon=-2.36,sport="rugby",fav_wins=False,score="Newcastle won",src="p.115"),
 dict(id="E18",name="FA Cup final 1998 Arsenal (fav) v Newcastle",dt="1998-05-16 15:00",tz=1,lat=51.51,lon=-0.13,sport="foot90et",fav_wins=True,score="Arsenal 2-0",src="p.116"),
 dict(id="E19",name="Scottish Cup final 1998 Rangers (fav) v Hearts",dt="1998-05-16 15:00",tz=1,lat=55.86,lon=-4.25,sport="foot90et",fav_wins=False,score="Hearts 2-1",src="p.116"),
 dict(id="T07",name="Super Bowl XXXIX Patriots (fav) v Eagles",dt="2005-02-06 18:38",tz=-5,lat=30.33,lon=-81.66,sport="usfoot",fav_wins=True,score="Patriots 24-21",src="App.4 test 7"),
 dict(id="T08",name="One-day cricket West Indies (fav) v Kenya, Poona",dt="1996-02-29 09:00",tz=5.5,lat=18.52,lon=73.86,sport="cricket1d",fav_wins=False,score="Kenya won",src="App.4 test 8"),
 dict(id="T09",name="Test Adelaide 2006 Australia (fav) v England",dt="2006-12-01 11:00",tz=10.5,lat=-34.93,lon=138.60,sport="crickettest",fav_wins=True,score="Australia won",src="App.4 test 9"),
 dict(id="T10",name="CL final 2002 Real Madrid (fav) v Leverkusen, Glasgow",dt="2002-05-15 19:45",tz=1,lat=55.86,lon=-4.25,sport="foot90et",fav_wins=True,score="Real 2-1",src="App.4 test 10"),
 dict(id="T11",name="League Cup final 2003 Man Utd (fav) v Liverpool, Cardiff",dt="2003-03-02 14:00",tz=0,lat=51.48,lon=-3.18,sport="foot90et",fav_wins=False,score="Liverpool 2-0",src="App.4 test 11"),
 dict(id="T12",name="World Cup final 1998 Brazil (fav) v France, Paris",dt="1998-07-12 21:00",tz=2,lat=48.92,lon=2.36,sport="foot90et",fav_wins=False,score="France 3-0",src="App.4 test 12"),
]
SPORT={ 'foot90':dict(range=5,et=False,draw=True),'foot90et':dict(range=6,et=True,draw=False),'usfoot':dict(range=4,et=False,draw=False),'baseball':dict(range=5,et=False,draw=False),
 'cricket1d':dict(range=13,et=False,draw=False),'crickettest':dict(range=None,et=False,draw=True),'tennis':dict(range=5,et=False,draw=False),'rugby':dict(range=5,et=False,draw=True)}
def utc(c):
    dt=datetime.strptime(c['dt'],"%Y-%m-%d %H:%M"); return dt-timedelta(hours=c['tz'])
