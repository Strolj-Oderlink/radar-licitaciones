# -*- coding: utf-8 -*-
"""Emite los tres entregables a partir de la ultima corrida."""
import json, os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reportes, dashboard
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get('MP_DATA') or os.path.join(ROOT, 'data')
OUT = os.environ.get('MP_OUT') or os.path.join(ROOT, 'salidas')
os.makedirs(OUT, exist_ok=True)
c = json.load(open(os.path.join(DATA, 'ultima_corrida.json'), encoding='utf-8'))
h, cerradas = reportes.actualizar_historico(c['filas'], dt.date.today().isoformat())
stamp = dt.date.today().strftime('%Y-%m-%d')
print(reportes.excel(c, c['filas'], cerradas, os.path.join(OUT, f'Licitaciones_MP_{stamp}.xlsx'), c.get('bajo_umbral', [])))
print(reportes.resumen_md(c, c['filas'], cerradas, os.path.join(OUT, f'Resumen_licitaciones_{stamp}.md')))
print(dashboard.build(c, c['filas'], c.get('bajo_umbral', []), os.path.join(OUT, f'Radar_licitaciones_{stamp}.html')))
