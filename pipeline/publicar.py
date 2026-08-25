# -*- coding: utf-8 -*-
"""Arma docs/ para GitHub Pages y devuelve el texto del aviso."""
import os, json, shutil, datetime as dt, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
OUT = os.environ.get('MP_OUT') or os.path.join(ROOT, 'salidas')
os.makedirs(DOCS, exist_ok=True)

htmls = sorted(glob.glob(os.path.join(OUT, 'Radar_licitaciones_*.html')))
if not htmls: raise SystemExit('no hay dashboard que publicar')
ultimo = htmls[-1]; stamp = os.path.basename(ultimo)[19:29]
# Una sola URL viva: index.html se sobreescribe en cada corrida.
shutil.copy(ultimo, os.path.join(DOCS, 'index.html'))
# El respaldo con nombre fijo permite descargarlo desde el mismo dominio sin adivinar la fecha.
for patron, destino in (('Licitaciones_MP_*.xlsx', 'licitaciones-ultima.xlsx'),
                        ('Resumen_licitaciones_*.md', 'resumen-ultimo.md')):
    hallados = sorted(glob.glob(os.path.join(OUT, patron)))
    if hallados:
        shutil.copy(hallados[-1], os.path.join(DOCS, destino))
# CNAME es lo que mantiene el dominio propio en GitHub Pages: no debe borrarse nunca.
cname = os.path.join(DOCS, 'CNAME')
if not os.path.exists(cname):
    open(cname, 'w').write('chilecompra.gamma-re.com\n')

c = json.load(open(os.path.join(ROOT, 'data', 'ultima_corrida.json'), encoding='utf-8'))
base = os.environ.get('PAGES_URL', '').rstrip('/')
print(json.dumps({'matches': len(c['filas']), 'stamp': stamp,
                  'url': base or '(configura PAGES_URL)'}, ensure_ascii=False))
open(os.path.join(ROOT, 'aviso.txt'), 'w', encoding='utf-8').write(
    f"Radar de licitaciones {dt.date.today():%d-%m}: {base}")
