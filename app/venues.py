"""Liste intégrée (secours) de grandes villes / stades européens : (alias..., lat, lon, fuseau IANA)."""
import unicodedata, re

def norm(s: str) -> str:
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()

# (noms/aliases séparés par |, lat, lon, tz)
_RAW = [
 # France
 ("Parc des Princes|Paris|Paris PSG", 48.8414, 2.2531, "Europe/Paris"),
 ("Stade de France|Saint-Denis", 48.9245, 2.3601, "Europe/Paris"),
 ("Stade Velodrome|Orange Velodrome|Marseille", 43.2699, 5.3959, "Europe/Paris"),
 ("Groupama Stadium|Decines|Lyon", 45.7653, 4.9822, "Europe/Paris"),
 ("Stade Pierre-Mauroy|Villeneuve-d'Ascq|Lille", 50.6119, 3.1304, "Europe/Paris"),
 ("Allianz Riviera|Nice", 43.7051, 7.1926, "Europe/Paris"),
 ("Stade Louis II|Monaco", 43.7277, 7.4156, "Europe/Monaco"),
 ("Roazhon Park|Rennes", 48.1075, -1.7128, "Europe/Paris"),
 ("Stade Bollaert-Delelis|Lens", 50.4328, 2.8153, "Europe/Paris"),
 ("Stade de la Beaujoire|Nantes", 47.2559, -1.5253, "Europe/Paris"),
 ("Stade Oceane|Le Havre", 49.4989, 0.1699, "Europe/Paris"),
 ("Stade Auguste-Delaune|Reims", 49.2465, 4.0250, "Europe/Paris"),
 ("Stade de la Mosson|Montpellier", 43.6222, 3.8120, "Europe/Paris"),
 ("Stade Matmut Atlantique|Bordeaux", 44.8974, -0.5616, "Europe/Paris"),
 ("Stadium de Toulouse|Toulouse", 43.5833, 1.4341, "Europe/Paris"),
 ("Stade de la Meinau|Strasbourg", 48.5601, 7.7553, "Europe/Paris"),
 # Angleterre / UK
 ("Wembley|Wembley Stadium", 51.5560, -0.2796, "Europe/London"),
 ("Emirates Stadium|Arsenal", 51.5549, -0.1084, "Europe/London"),
 ("Stamford Bridge|Chelsea", 51.4817, -0.1910, "Europe/London"),
 ("Old Trafford|Manchester United", 53.4631, -2.2913, "Europe/London"),
 ("Etihad Stadium|Manchester City|Manchester", 53.4831, -2.2004, "Europe/London"),
 ("Anfield|Liverpool", 53.4308, -2.9608, "Europe/London"),
 ("Goodison Park|Everton|Hill Dickinson Stadium", 53.4388, -2.9664, "Europe/London"),
 ("Tottenham Hotspur Stadium|Tottenham", 51.6042, -0.0662, "Europe/London"),
 ("London Stadium|West Ham", 51.5387, -0.0166, "Europe/London"),
 ("Villa Park|Aston Villa|Birmingham", 52.5092, -1.8847, "Europe/London"),
 ("St James' Park|Newcastle", 54.9756, -1.6217, "Europe/London"),
 ("Hampden Park|Glasgow", 55.8259, -4.2520, "Europe/London"),
 ("Celtic Park", 55.8497, -4.2056, "Europe/London"),
 ("Ibrox|Ibrox Stadium", 55.8533, -4.3092, "Europe/London"),
 ("Millennium Stadium|Principality Stadium|Cardiff", 51.4782, -3.1826, "Europe/London"),
 ("Selhurst Park|Crystal Palace", 51.3983, -0.0856, "Europe/London"),
 ("London", 51.5074, -0.1278, "Europe/London"),
 ("Edinburgh", 55.9533, -3.1883, "Europe/London"),
 ("Dublin|Aviva Stadium", 53.3351, -6.2285, "Europe/Dublin"),
 # Espagne / Portugal
 ("Santiago Bernabeu|Real Madrid|Madrid", 40.4531, -3.6883, "Europe/Madrid"),
 ("Metropolitano|Civitas Metropolitano|Atletico Madrid", 40.4362, -3.5995, "Europe/Madrid"),
 ("Camp Nou|Spotify Camp Nou|Barcelona|Barcelone", 41.3809, 2.1228, "Europe/Madrid"),
 ("Montjuic|Estadi Olimpic Lluis Companys", 41.3647, 2.1556, "Europe/Madrid"),
 ("Mestalla|Valencia|Valence", 39.4747, -0.3583, "Europe/Madrid"),
 ("Ramon Sanchez-Pizjuan|Sevilla|Seville", 37.3840, -5.9705, "Europe/Madrid"),
 ("Benito Villamarin|Real Betis", 37.3565, -5.9817, "Europe/Madrid"),
 ("San Mames|Bilbao|Athletic Club", 43.2641, -2.9494, "Europe/Madrid"),
 ("Reale Arena|Anoeta|San Sebastian|Real Sociedad", 43.3014, -1.9737, "Europe/Madrid"),
 ("Estadio da Luz|Lisbon|Lisbonne|Benfica", 38.7527, -9.1847, "Europe/Lisbon"),
 ("Estadio Jose Alvalade|Sporting CP", 38.7615, -9.1608, "Europe/Lisbon"),
 ("Estadio do Dragao|Porto|FC Porto", 41.1617, -8.5836, "Europe/Lisbon"),
 # Italie
 ("San Siro|Giuseppe Meazza|Milan|Milano|Inter", 45.4781, 9.1240, "Europe/Rome"),
 ("Allianz Stadium|Juventus Stadium|Turin|Torino|Juventus", 45.1096, 7.6412, "Europe/Rome"),
 ("Stadio Olimpico|Rome|Roma|Lazio", 41.9340, 12.4547, "Europe/Rome"),
 ("Diego Armando Maradona|Stadio San Paolo|Napoli|Naples", 40.8280, 14.1931, "Europe/Rome"),
 ("Stadio Artemio Franchi|Florence|Fiorentina", 43.7809, 11.2825, "Europe/Rome"),
 ("Stadio Renato Dall'Ara|Bologna", 44.4924, 11.3097, "Europe/Rome"),
 ("Gewiss Stadium|Bergamo|Atalanta", 45.7089, 9.6808, "Europe/Rome"),
 ("Stadio Luigi Ferraris|Genoa|Genes", 44.4165, 8.9520, "Europe/Rome"),
 # Allemagne / Autriche / Suisse
 ("Allianz Arena|Munich|Bayern", 48.2188, 11.6247, "Europe/Berlin"),
 ("Signal Iduna Park|Westfalenstadion|Dortmund", 51.4926, 7.4519, "Europe/Berlin"),
 ("Olympiastadion Berlin|Berlin|Hertha", 52.5147, 13.2395, "Europe/Berlin"),
 ("Red Bull Arena Leipzig|Leipzig", 51.3459, 12.3483, "Europe/Berlin"),
 ("BayArena|Leverkusen", 51.0383, 7.0022, "Europe/Berlin"),
 ("Veltins-Arena|Gelsenkirchen|Schalke", 51.5545, 7.0678, "Europe/Berlin"),
 ("Deutsche Bank Park|Frankfurt|Francfort", 50.0686, 8.6455, "Europe/Berlin"),
 ("Volksparkstadion|Hamburg|Hambourg", 53.5871, 9.8987, "Europe/Berlin"),
 ("Mercedes-Benz Arena|MHPArena|Stuttgart", 48.7923, 9.2320, "Europe/Berlin"),
 ("Borussia-Park|Monchengladbach", 51.1746, 6.3855, "Europe/Berlin"),
 ("Weserstadion|Bremen|Breme", 53.0664, 8.8376, "Europe/Berlin"),
 ("Wien|Vienna|Vienne|Ernst Happel", 48.2082, 16.3738, "Europe/Vienna"),
 ("Basel|Bale|St. Jakob-Park", 47.5415, 7.6204, "Europe/Zurich"),
 ("Zurich|Zuerich", 47.3769, 8.5417, "Europe/Zurich"),
 # Benelux
 ("Johan Cruijff ArenA|Amsterdam", 52.3144, 4.9419, "Europe/Amsterdam"),
 ("De Kuip|Feyenoord|Rotterdam", 51.8939, 4.5231, "Europe/Amsterdam"),
 ("Philips Stadion|Eindhoven|PSV", 51.4417, 5.4675, "Europe/Amsterdam"),
 ("Jan Breydel|Bruges|Brugge|Club Brugge", 51.1932, 3.1806, "Europe/Brussels"),
 ("Constant Vanden Stock|Anderlecht|Brussels|Bruxelles", 50.8341, 4.2985, "Europe/Brussels"),
 # Autres
 ("Istanbul|Ataturk Olimpiyat|Besiktas|Galatasaray|Fenerbahce|Ali Sami Yen|Rams Park", 41.0082, 28.9784, "Europe/Istanbul"),
 ("Athens|Athenes|OAKA|Olympiacos|Panathinaikos", 37.9838, 23.7275, "Europe/Athens"),
 ("Belgrade|Rajko Mitic|Crvena Zvezda", 44.7866, 20.4489, "Europe/Belgrade"),
 ("Zagreb|Maksimir|Dinamo Zagreb", 45.8150, 15.9819, "Europe/Zagreb"),
 ("Prague|Praha|Sparta Praha|Slavia Praha", 50.0755, 14.4378, "Europe/Prague"),
 ("Warsaw|Varsovie|Warszawa", 52.2297, 21.0122, "Europe/Warsaw"),
 ("Budapest|Puskas Arena", 47.4979, 19.0402, "Europe/Budapest"),
 ("Copenhagen|Copenhague|Parken", 55.6761, 12.5683, "Europe/Copenhagen"),
 ("Stockholm", 59.3293, 18.0686, "Europe/Stockholm"),
 ("Oslo", 59.9139, 10.7522, "Europe/Oslo"),
 ("Helsinki", 60.1699, 24.9384, "Europe/Helsinki"),
 ("Kyiv|Kiev|Kiyv", 50.4501, 30.5234, "Europe/Kyiv"),
 ("Moscow|Moscou|Luzhniki", 55.7558, 37.6173, "Europe/Moscow"),
 ("Bucharest|Bucarest", 44.4268, 26.1025, "Europe/Bucharest"),
 ("Sofia", 42.6977, 23.3219, "Europe/Sofia"),
 ("Bratislava", 48.1486, 17.1077, "Europe/Bratislava"),
 ("Ljubljana", 46.0569, 14.5058, "Europe/Ljubljana"),
 ("Tel Aviv", 32.0853, 34.7818, "Asia/Jerusalem"),
 ("Baku|Bakou", 40.4093, 49.8671, "Asia/Baku"),
 # Hors Europe (quelques grandes villes)
 ("New York|MetLife Stadium", 40.7128, -74.0060, "America/New_York"),
 ("Buenos Aires|La Bombonera|Monumental", -34.6037, -58.3816, "America/Argentina/Buenos_Aires"),
 ("Rio de Janeiro|Maracana", -22.9068, -43.1729, "America/Sao_Paulo"),
 ("Sao Paulo", -23.5505, -46.6333, "America/Sao_Paulo"),
]
VENUES = []
for names, lat, lon, tz in _RAW:
    al = [norm(n) for n in names.split('|')]
    VENUES.append((al, lat, lon, tz, names.split('|')[0]))

def lookup(*queries):
    """Cherche d'abord un alias exact (stade), puis un alias contenu dans la requête (ville)."""
    qs = [norm(q) for q in queries if q]
    for q in qs:
        for al, lat, lon, tz, label in VENUES:
            if q in al:
                return dict(lat=lat, lon=lon, tz=tz, label=label)
    for q in qs:
        for al, lat, lon, tz, label in VENUES:
            for a in al:
                if len(a) >= 5 and re.search(r'\b' + re.escape(a) + r'\b', q):
                    return dict(lat=lat, lon=lon, tz=tz, label=label)
    return None
