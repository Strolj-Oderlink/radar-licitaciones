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
#
# GitHub documenta que los eventos programados se retrasan con carga alta y que,
# si la carga es suficiente, los trabajos encolados se DESCARTAN. Por eso el
# workflow dispara varias veces dentro de cada ventana (y en un minuto fuera del
# peak): basta con que uno de los intentos sobreviva. El primero que entra marca
# estado_ejecucion.json y los demas se omiten solos.
VENTANAS = {0: (11, 13), 2: (21, 23)}

# Red de seguridad: si GitHub descarto todos los intentos de la semana, o deshabilito
# el schedule por inactividad, una corrida de recuperacion evita quedar ciego.
RETRASO_MAXIMO_DIAS = 4
forzar = os.environ.get('FORZAR', '').lower() in ('1', 'true', 'yes')

rango = VENTANAS.get(ahora.weekday())
ok = bool(rango and rango[0] <= ahora.hour <= rango[1])
hoy = ahora.date().isoformat()
try: prev = json.load(open(EST))
except Exception: prev = {}
ya_corrio = prev.get('ultima_corrida') == hoy

# Recuperacion: si hace demasiado que no hay corrida efectiva, correr igual.
dias_sin_correr = None
if prev.get('ultima_corrida'):
    try:
        dias_sin_correr = (ahora.date() - dt.date.fromisoformat(prev['ultima_corrida'])).days
    except ValueError:
        pass
recuperacion = (dias_sin_correr is not None
                and dias_sin_correr >= RETRASO_MAXIMO_DIAS
                and not ya_corrio)

correr = forzar or (ok and not ya_corrio) or recuperacion
print(f"hora Santiago: {ahora:%Y-%m-%d %H:%M} ({['lun','mar','mie','jue','vie','sab','dom'][ahora.weekday()]}) "
      f"| en ventana: {ok} | ya corrio hoy: {ya_corrio} | dias sin correr: {dias_sin_correr} "
      f"| forzar: {forzar} | recuperacion: {recuperacion} -> {'CORRER' if correr else 'OMITIR'}")
if recuperacion and not ok:
    print(f"::warning title=Corrida de recuperacion::Pasaron {dias_sin_correr} dias sin corrida "
          f"efectiva. GitHub pudo haber descartado los disparos programados. Se ejecuta fuera "
          f"de la ventana habitual para no quedar sin datos.")
with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
    f.write(f"correr={'true' if correr else 'false'}\n")
resumen = os.environ.get('GITHUB_STEP_SUMMARY')
dia = ['lunes','martes','miercoles','jueves','viernes','sabado','domingo'][ahora.weekday()]

if correr:
    os.makedirs(os.path.dirname(EST), exist_ok=True)
    json.dump({'ultima_corrida': hoy, 'hora': ahora.isoformat()}, open(EST, 'w'))
    if resumen:
        open(resumen, 'a').write(
            f"## Radar ejecutandose\n\n{dia} {ahora:%d-%m-%Y %H:%M} hora de Santiago.\n\n")
else:
    # Este es el caso que mas confunde: el job termina en verde, todos los pasos quedan
    # omitidos y no llega ni correo ni WhatsApp. Hay que decirlo con todas sus letras.
    motivo = ('ya se ejecuto hoy' if ya_corrio else
              f'{dia} {ahora:%H:%M} no es ventana de ejecucion (lunes 11:00 / miercoles 21:00)')
    print(f"::notice title=Corrida omitida::{motivo}. No se publicara dashboard ni se enviaran "
          f"avisos. Para ejecutar igual: Run workflow con la casilla 'forzar' marcada.")
    if resumen:
        open(resumen, 'a').write(
            f"## Corrida omitida\n\n**Motivo:** {motivo}.\n\n"
            f"Los pasos siguientes aparecen como omitidos y **no** se publico el dashboard "
            f"ni se envio correo o WhatsApp. Esto no es un error.\n\n"
            f"Para forzar una corrida fuera de horario: *Run workflow* con **forzar** marcado.\n\n")
