# -*- coding: utf-8 -*-
"""Decide si esta ejecucion corresponde a una ventana valida en hora de Chile.

GitHub Actions programa en UTC y Chile cambia de huso (UTC-4 / UTC-3), asi que el
workflow dispara en los dos horarios posibles y este guardia deja pasar solo el
que cae en la hora local correcta. Ademas evita la corrida doble del mismo dia.
"""
import os, json, sys, datetime as dt
try:
    from zoneinfo import ZoneInfo
    ahora = dt.datetime.now(ZoneInfo('America/Santiago'))
except Exception:
    ahora = dt.datetime.utcnow() - dt.timedelta(hours=4)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EST = os.path.join(ROOT, 'data', 'estado_ejecucion.json')

# Objetivo: lunes 11:00 y miercoles 21:00, hora de Santiago.
# El workflow dispara en los dos horarios UTC posibles (UTC-4 y UTC-3); solo uno
# de ellos cae en la hora local correcta y el otro se descarta aqui. El margen de
# una hora extra absorbe el atraso tipico del scheduler de GitHub Actions.
VENTANAS = {0: (11, 12), 2: (21, 22)}
forzar = os.environ.get('FORZAR', '').lower() in ('1', 'true', 'yes')

rango = VENTANAS.get(ahora.weekday())
ok = bool(rango and rango[0] <= ahora.hour <= rango[1])
hoy = ahora.date().isoformat()
try: prev = json.load(open(EST))
except Exception: prev = {}
ya_corrio = prev.get('ultima_corrida') == hoy

correr = forzar or (ok and not ya_corrio)
print(f"hora Santiago: {ahora:%Y-%m-%d %H:%M} ({['lun','mar','mie','jue','vie','sab','dom'][ahora.weekday()]}) "
      f"| en ventana: {ok} | ya corrio hoy: {ya_corrio} | forzar: {forzar} -> {'CORRER' if correr else 'OMITIR'}")
with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
    f.write(f"correr={'true' if correr else 'false'}\n")
if correr:
    os.makedirs(os.path.dirname(EST), exist_ok=True)
    json.dump({'ultima_corrida': hoy, 'hora': ahora.isoformat()}, open(EST, 'w'))
