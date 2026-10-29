"""Captures d'écran de l'UI (nécessite : pip install playwright + Chrome/Chromium installé)."""
import sys
from playwright.sync_api import sync_playwright
url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8000'
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    pg = b.new_page(viewport={'width': 1100, 'height': 900})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    pg.goto(url); pg.wait_for_selector('.m', timeout=60000)
    pg.screenshot(path='docs_ecran1_choix.png')
    pg.click('.m >> nth=0'); pg.wait_for_selector('#fav')
    pg.select_option('#fav', index=1 if pg.input_value('#fav') == '' else None) if pg.input_value('#fav') == '' else None
    pg.click('#btnPredict'); pg.wait_for_selector('.verdict', timeout=60000)
    pg.screenshot(path='docs_ecran2_resultat.png', full_page=True)
    m = b.new_page(viewport={'width': 390, 'height': 800}, device_scale_factor=2)
    m.goto(url); m.wait_for_selector('.m', timeout=60000); m.click('.m >> nth=0'); m.wait_for_selector('#fav')
    if m.input_value('#fav') == '': m.select_option('#fav', index=1)
    m.click('#btnPredict'); m.wait_for_selector('.verdict', timeout=60000); m.wait_for_timeout(800)
    m.screenshot(path='docs_ecran3_mobile.png', full_page=True)
    print('erreurs JS:', errs)
    b.close()
