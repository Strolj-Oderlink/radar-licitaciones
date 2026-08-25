# -*- coding: utf-8 -*-
"""Envia el Excel de respaldo por correo usando la API de Resend."""
import os, json, glob, base64, urllib.request, urllib.error, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get('MP_OUT') or os.path.join(ROOT, 'salidas')
DATA = os.environ.get('MP_DATA') or os.path.join(ROOT, 'data')

API = 'https://api.resend.com/emails'
DESTINO = os.environ.get('EMAIL_DESTINO', 'luisfelipe@realsachile.com')
REMITENTE = os.environ.get('EMAIL_REMITENTE', 'Radar de Licitaciones <radar@envios.gamma-re.com>')
PAGES = os.environ.get('PAGES_URL', 'https://chilecompra.gamma-re.com').rstrip('/')


def cuerpo(c, nuevas, urgentes):
    f = ('<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#111820;'
         'line-height:1.55;max-width:640px">')
    f += f'<h2 style="margin:0 0 4px;color:#1f3b57">Radar de licitaciones — {dt.date.today():%d-%m-%Y}</h2>'
    f += (f'<p style="color:#5d6b7a;margin:0 0 18px">{len(c["filas"])} licitaciones vigentes calzan con '
          f'Gamma / Realsa Brokers · <strong style="color:#1e7a4b">{len(nuevas)} nuevas</strong> '
          f'esta corrida · {len(urgentes)} cierran dentro de 7 días.</p>')
    if nuevas:
        f += '<h3 style="color:#1e7a4b;font-size:15px;margin:0 0 8px">Nuevas en el radar</h3><ul style="padding-left:18px;margin:0 0 18px">'
        for r in nuevas[:10]:
            d = r.get('Dias al cierre')
            f += (f'<li style="margin-bottom:7px"><a href="{r["URL"]}" style="color:#1f3b57;font-weight:bold">'
                  f'{r["Nombre"][:95]}</a><br><span style="color:#5d6b7a;font-size:12.5px">'
                  f'{r["Organismo"]} · {r["Region"]} · {r["Tipo de oportunidad"]} · '
                  f'{r["Monto publicado"]}{f" · cierra en {d} d" if d is not None else ""} → {r["Entidad sugerida"]}'
                  f'</span></li>')
        f += '</ul>'
    if urgentes:
        f += '<h3 style="color:#a32626;font-size:15px;margin:0 0 8px">Cierran dentro de 7 días</h3><ul style="padding-left:18px;margin:0 0 18px">'
        for r in sorted(urgentes, key=lambda x: x['Dias al cierre'])[:10]:
            f += (f'<li style="margin-bottom:5px"><strong>{r["Dias al cierre"]}d</strong> — '
                  f'<a href="{r["URL"]}" style="color:#1f3b57">{r["Nombre"][:85]}</a></li>')
        f += '</ul>'
    f += (f'<p style="margin:20px 0"><a href="{PAGES}" style="background:#1f3b57;color:#fff;'
          f'text-decoration:none;padding:11px 20px;border-radius:6px;display:inline-block">'
          f'Abrir el dashboard</a></p>')
    f += ('<p style="color:#5d6b7a;font-size:12px;border-top:1px solid #e2e6ea;padding-top:12px">'
          'El Excel adjunto trae el histórico acumulado, los avisos bajo umbral y la hoja de '
          'descartes auditables. La columna <strong>Nueva</strong> marca con SI lo que no aparecía '
          'en ninguna corrida anterior.<br>Mensaje automático del radar de licitaciones.</p></div>')
    return f


def main():
    key = os.environ.get('RESEND_API_KEY', '').strip()
    if not key:
        print('[correo] falta RESEND_API_KEY; no se envia'); return
    xlsx = sorted(glob.glob(os.path.join(OUT, 'Licitaciones_MP_*.xlsx')))
    if not xlsx:
        print('[correo] no hay Excel que adjuntar'); return
    xlsx = xlsx[-1]
    c = json.load(open(os.path.join(DATA, 'ultima_corrida.json'), encoding='utf-8'))
    nuevas = [r for r in c['filas'] if r.get('Novedad') == 'NUEVA']
    urgentes = [r for r in c['filas'] if r.get('Dias al cierre') is not None and r['Dias al cierre'] <= 7]

    asunto = (f"Radar de licitaciones {dt.date.today():%d-%m-%Y} — "
              f"{len(nuevas)} nuevas, {len(c['filas'])} vigentes")
    payload = {
        'from': REMITENTE, 'to': [DESTINO], 'subject': asunto,
        'html': cuerpo(c, nuevas, urgentes),
        'attachments': [{
            'filename': os.path.basename(xlsx),
            'content': base64.b64encode(open(xlsx, 'rb').read()).decode(),
        }],
    }
    # El User-Agent NO es opcional: Resend esta detras de Cloudflare, que bloquea el
    # cliente por defecto de urllib ('Python-urllib/3.x') con 403 y "error code: 1010".
    req = urllib.request.Request(API, data=json.dumps(payload).encode(),
                                 headers={'Authorization': f'Bearer {key}',
                                          'Content-Type': 'application/json',
                                          'Accept': 'application/json',
                                          'User-Agent': 'radar-licitaciones/1.0'})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        print(f"[correo] enviado a {DESTINO} · id {r.get('id')} · adjunto {os.path.basename(xlsx)}")
    except urllib.error.HTTPError as e:
        detalle = e.read().decode('utf-8', 'ignore')[:400]
        print(f"[correo] error {e.code}: {detalle}")
        if e.code == 403 and '1010' in detalle:
            print("[correo] Bloqueo de Cloudflare por el User-Agent del cliente.")
        elif e.code == 403:
            print("[correo] Resend rechazo el envio. Revisa que el dominio del remitente "
                  f"({REMITENTE}) sea uno verificado en Domains.")
        elif e.code == 401:
            print("[correo] La RESEND_API_KEY no es valida o no tiene permiso de envio.")
        raise
    except Exception as e:
        print(f"[correo] fallo: {str(e)[:300]}"); raise


if __name__ == '__main__':
    main()
