# Astro-Foot — prédiction de matchs de football selon la méthode de John Frawley

Application web (FastAPI + HTML/CSS/JS statique) qui applique la méthode **« thème d'événement »** du chapitre 2 de
*Sports Astrology* (John Frawley, 2007) : thème dressé pour le **coup d'envoi** et le **stade**, maisons Placidus,
**favori = maisons 1 et 10, outsider = maisons 7 et 4**, aspects de la Lune, Part de Fortune et son antiscion, Nœuds, combustion, Pluton…
On choisit un match → bouton « Prédire » → vainqueur (ou « indéterminé »), score indicatif, niveau de confiance et **liste explicite des témoignages** en français.

> ⚠️ **Divertissement / étude de la méthode uniquement.** Aucune validité statistique n'est démontrée (le livre ne donne que des anecdotes).
> Les poids et priorités entre témoignages sont des **hypothèses d'implémentation** (le livre n'en fournit aucun), réglées sur 25 thèmes du livre :
> ce n'est pas une validation hors échantillon. **Aucun taux de réussite n'est revendiqué.** Ne pas utiliser pour parier.

## Installation
```bash
cd /workspace/frawley-app
python3 -m venv ve && ve/bin/pip install -r requirements.txt     # (ou : uv venv ve && uv pip install -r requirements.txt)
./run.sh                      # http://localhost:8000   (HOST=0.0.0.0 PORT=8000 par défaut)
```
Documentation interactive de l'API : `http://localhost:8000/docs`.

## Variables d'environnement
| Variable | Rôle |
|---|---|
| `FOOTBALL_DATA_API_KEY` | Active l'import automatique via football-data.org (clé gratuite sur football-data.org). Sans elle, ESPN (sans clé) est utilisé. |
| `NOMINATIM_USER_AGENT` | User-Agent envoyé à Nominatim (la politique d'OSM impose un UA identifiable : mettez votre contact). |
| `NOMINATIM_URL` | Autre instance Nominatim (défaut : nominatim.openstreetmap.org). |
| `FIXTURES_TTL` | Durée du cache du calendrier en secondes (défaut 900). |
| `FRAWLEY_DATA_DIR` | Dossier du cache de géocodage `geocache.json` (défaut `./data`). |
| `HOST`, `PORT` | Adresse/port d'écoute de `run.sh`. |

## Ce qui est automatique / manuel (vérifié depuis la box le 28/10/2026)
- **Calendrier automatique, sans clé : ESPN** (API publique non officielle `site.api.espn.com`) : 17 compétitions (Ligue 1, Premier League, LaLiga, Bundesliga, Serie A, Liga Portugal, Eredivisie, Pro League, C1/C3/C4, coupes nationales), coup d'envoi UTC, stade + ville, **cotes moneyline (DraftKings)**. Peut changer sans préavis.
- **Favori** : présélectionné d'après les cotes (cote la plus basse ; rapport < 1,10 = « égalité » [HYP]) mais **modifiable** ; si pas de cotes, l'utilisateur choisit. Les cotes ne servent qu'à désigner le favori. Égalité ⇒ « méthode inutilisable » (Frawley p.79) ⇒ résultat « indéterminé ».
- **football-data.org** : code prêt (`app/fixtures.py::from_football_data`), s'active avec `FOOTBALL_DATA_API_KEY` (non testé : pas de clé ; sans clé l'API répond mais ne renvoie rien d'utile). Pas de cotes dans l'offre gratuite.
- **OpenLigaDB** (sans clé, Bundesliga/DFB-Pokal, sans stade ni cotes) : utilisé seulement si ESPN échoue.
- **Saisie manuelle** : formulaire (équipes, date, heure locale, stade/ville) avec 3 exemples pré-remplis ; toujours disponible. L'UI indique clairement « automatique » ou « manuel ».
- **Géocodage** : cache disque → Nominatim (1 requête/s) → liste intégrée de ~100 grandes villes/stades (`app/venues.py`). Fuseau par `timezonefinder`, conversion heure locale → UTC par `zoneinfo` (heure d'été correcte, détection des heures inexistantes/ambiguës).

## API
`POST /api/predict` — corps JSON :
```json
{"equipe_a":"PSG","equipe_b":"OM","favori":"a","date":"2026-11-01","heure":"21:00",
 "stade":"Parc des Princes","ville":"Paris","pays":"France","elimination":false}
```
- `favori` : `"a"`, `"b"` ou `"egal"` ; lieu : `stade`/`ville`/`pays` **ou** `lat`+`lon` (+ `fuseau` IANA ou `utc_offset`) ; heure : `date`+`heure` locales **ou** `kickoff_utc` (`AAAA-MM-JJ HH:MM`) ; `elimination:true` = prolongation possible (plage de la Lune 6° au lieu de 5°).
- Réponse : `match`, `theme` (ASC, MC, DSC, IC, Lune, Fortuna + antiscion, Nœuds, planètes, maisons des équipes, seigneurs), `prediction` (`resultat` = `a|b|nul|indetermine`, `vainqueur`, `score`, `confiance`, `raisonnement`), `temoignages[]` (équipe, poids, niveau, texte français, source du livre, `decisif`), `sequence_lune[]`, `avertissements[]`, `mentions`.
- Autres : `GET /api/matches?days=7[&refresh=true]`, `GET /api/geocode?q=…`, `GET /api/cases` (les 25 cas), `GET /api/status`.
- Le paramètre `sport` n'existe que pour rejouer les cas non-football du livre (tests) ; l'application est **limitée au football**.

## Tests
```bash
ve/bin/pytest -q tests/test_api.py                 # tests fonctionnels (DST, géocodage de secours, API, validation)
ve/bin/python tests/run_book_cases.py              # les 25 cas du livre via POST /api/predict (serveur lancé) ; « inproc » = sans serveur
ve/bin/python tests/screenshot.py                  # captures d'écran (nécessite playwright + Chrome)
```
Résultat des 25 cas : **24/25 vainqueurs « retrouvés »** (échec connu : E15, Ashes Perth 2006). **Attention : les poids ont été réglés sur ces mêmes 25 cas**, ce n'est donc pas une mesure de capacité prédictive ; la référence « toujours favori » donne 11/25 (le livre choisit surtout des surprises). Score exact (9 matchs de foot du livre avec score) : 3/9, purement indicatif.

## Structure
```
app/main.py            API FastAPI + pages statiques
app/engine/            frawley_event.py (thème : ephem), judge_fr.py (règles/poids + explications FR), cases.py (25 cas)
app/geo.py, venues.py  géocodage + fuseaux ; app/fixtures.py  sources de matchs
static/                index.html, style.css, app.js (roue SVG, liste des témoignages)
tests/                 test_api.py, run_book_cases.py, screenshot.py ; docs/ captures
```

## Limites connues
- Le **favori** ne se déduit pas du thème ; il vient des cotes ou de l'utilisateur. Cotes ESPN/DraftKings = une seule source.
- Pondérations [HYP] et surajustement possible ; E15 reste en échec ; Saturne « malefic », Neptune, étoiles fixes non implémentés.
- Le **score** est une heuristique (« educated guess » p.91) : 2-0/2-1 a priori ; à ne pas prendre au sérieux. Le « match nul » (championnat, témoignages qui se compensent) est une hypothèse non issue du livre et non testée.
- Méthode peu pertinente quand beaucoup de matchs partent à la même heure (samedi 15 h) : avertissement affiché.
- Calcul astronomique : `ephem` + formules maison (précision ≈ 1′ sur les exemples), nœud lunaire vrai approché (Meeus), pas de Swiss Ephemeris.
- Latitudes > 66° refusées. ESPN est une API non officielle ; Nominatim impose 1 requête/s et un User-Agent identifiable.
