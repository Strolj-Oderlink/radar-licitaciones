# -*- coding: utf-8 -*-
"""Envia el aviso de WhatsApp via CallMeBot. Solo el link, por decision del usuario."""
import os, sys, urllib.parse, urllib.request, datetime as dt

def enviar(texto):
    phone = os.environ.get('WHATSAPP_PHONE', '').strip()
    apikey = os.environ.get('CALLMEBOT_APIKEY', '').strip()
    if not phone or not apikey:
        print('[notificar] falta WHATSAPP_PHONE o CALLMEBOT_APIKEY; no se envia'); return False
    url = ('https://api.callmebot.com/whatsapp.php?'
           + urllib.parse.urlencode({'phone': phone, 'text': texto, 'apikey': apikey}))
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'radar-licitaciones/1.0'})
        r = urllib.request.urlopen(req, timeout=45).read().decode('utf-8', 'ignore')
        print('[notificar] respuesta CallMeBot:', r[:200])
        return True
    except Exception as e:
        print('[notificar] fallo el envio:', str(e)[:200]); return False

if __name__ == '__main__':
    enviar(sys.argv[1] if len(sys.argv) > 1 else 'Radar de licitaciones actualizado')
