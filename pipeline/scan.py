# -*- coding: utf-8 -*-
"""Barrido de Mercado Publico -> licitaciones que calzan con Gamma / Realsa Brokers."""
import json, os, sys, time, argparse, urllib.request, urllib.error, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from taxonomia import (norm, puntuar, excluido, clasificar_oportunidad, NUCLEO, OBJETO, VERBO_CONTEXTUAL,
                       EXCLUYENTES, UMBRAL_MATCH, UMBRAL_ALTO)

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get('MP_DATA') or os.path.join(BASE, 'data')
CACHE = os.path.join(DATA, 'cache_detalles.json')
HIST  = os.path.join(DATA, 'historico.json')
API = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
TICKET = os.environ.get('MP_TICKET', 'F8537A18-6766-4DEF-9E59-426B4FEE2844')

def log(m): print(f"[{dt.datetime.now():%H:%M:%S}] {m}", flush=True)

def get_json(url, intentos=6):
    espera = 1.5
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            return json.loads(urllib.request.urlopen(req, timeout=45).read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(espera); espera = min(espera * 1.8, 20); continue
            if i == intentos - 1: raise
            time.sleep(espera)
        except Exception:
            if i == intentos - 1: raise
            time.sleep(espera); espera *= 1.6
    return None

def uf_hoy():
    try:
        req = urllib.request.Request("https://mindicador.cl/api/uf", headers={'User-Agent':'Mozilla/5.0'})
        d = json.loads(urllib.request.urlopen(req, timeout=25).read())
        return float(d['serie'][0]['valor']), d['serie'][0]['fecha'][:10]
    except Exception:
        return 40864.55, 'fallback'

# ------------------------------------------------------------ etapa 1: listado
def listado_activas():
    d = get_json(f"{API}?estado=activas&ticket={TICKET}")
    return d.get('Listado', [])

def prefiltro(nombre):
    """Filtro barato sobre el titulo: decide a quien le pedimos el detalle."""
    n = norm(nombre)
    if excluido(nombre): return False
    return any(k in n for k in NUCLEO) or any(k in n for k in OBJETO) \
           or any(k in n for k in VERBO_CONTEXTUAL)

# ------------------------------------------------------------ etapa 2: detalle
def cargar(p, default):
    if os.path.exists(p):
        try: return json.load(open(p, encoding='utf-8'))
        except Exception: return default
    return default

def detalles(codigos, cache, pausa=1.1, presupuesto=None):
    nuevos = [c for c in codigos if c not in cache]
    log(f"detalles: {len(codigos)} candidatos, {len(nuevos)} sin cachear")
    t0 = time.time()
    for i, c in enumerate(nuevos, 1):
        if presupuesto and time.time() - t0 > presupuesto:
            log(f"  presupuesto agotado en {i-1}/{len(nuevos)}; caché guardado, reanudable")
            break
        try:
            d = get_json(f"{API}?codigo={c}&ticket={TICKET}")
            lst = d.get('Listado') or []
            cache[c] = lst[0] if lst else {}
        except Exception as e:
            log(f"  fallo {c}: {str(e)[:60]}"); cache[c] = {}
        if i % 25 == 0:
            log(f"  {i}/{len(nuevos)}"); json.dump(cache, open(CACHE,'w',encoding='utf-8'), ensure_ascii=False)
        time.sleep(pausa)
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    return cache

# ------------------------------------------------------------ etapa 3: reglas
REGIONES_RM = ('metropolitana',)

# Tipo de licitacion -> rango legal de monto en UTM (Ley 19.886). Sirve de proxy
# cuando el organismo oculta el monto estimado (VisibilidadMonto = 0).
RANGO_TIPO = {
    'L1': '< 100 UTM (~< UF 170)', 'LE': '100-1.000 UTM (~UF 170-1.700)',
    'LP': '1.000-2.000 UTM (~UF 1.700-3.400)', 'LQ': '2.000-5.000 UTM (~UF 3.400-8.600)',
    'LR': '> 5.000 UTM (~> UF 8.600)', 'LS': 'servicios personales especializados',
    'E2': 'obras < 100 UTM', 'CO': 'obras 100-1.000 UTM', 'B2': 'obras 1.000-5.000 UTM',
    'H2': 'obras 5.000-40.000 UTM', 'I2': 'obras > 40.000 UTM',
}

def monto_uf(det, uf):
    m = det.get('MontoEstimado')
    mon = (det.get('Moneda') or 'CLP').upper()
    if not m or float(m) <= 0: return None, 'no publicado'
    m = float(m)
    if mon in ('CLP', 'CLP$', 'PESOS'): return m / uf, f"CLP {m:,.0f}"
    if mon in ('UF',): return m, f"UF {m:,.0f}"
    if mon in ('USD', 'DOLAR'): return m * 950 / uf, f"USD {m:,.0f}"
    if mon in ('EUR',): return m * 1050 / uf, f"EUR {m:,.0f}"
    return m / uf, f"{mon} {m:,.0f}"

def aplica_umbral(uf_val, region, min_rm, min_nac):
    """Nacional > min_nac UF ; RM > min_rm UF. Monto oculto => pasa marcado."""
    es_rm = any(r in norm(region) for r in REGIONES_RM)
    if uf_val is None:
        return True, ('RM' if es_rm else 'Nacional') + ' / monto no publicado'
    def n(v): return f"{v:,.0f}".replace(',', '.')
    if es_rm:
        return uf_val >= min_rm, f"RM, UF {n(uf_val)} (umbral UF {n(min_rm)})"
    return uf_val >= min_nac, f"Nacional, UF {n(uf_val)} (umbral UF {n(min_nac)})"

def asignar_entidad(det, uf_val, score):
    """Gamma y Realsa venden lo mismo; Gamma tiene historia verificable.
    Regla: donde el pliego pesa experiencia acreditada -> Gamma."""
    txt = norm(det.get('Nombre','') + ' ' + (det.get('Descripcion') or ''))
    tipo = (det.get('Tipo') or '').upper()
    senal_exp = any(k in txt for k in ('experiencia','acreditar','antecedentes similares',
                    'trayectoria','curriculum','trabajos anteriores','años de experiencia'))
    grande = tipo in ('LP','LQ','LR','LS') or (uf_val or 0) >= 2000
    if senal_exp or grande:
        return 'Gamma', 'exige/pondera experiencia acreditable o es licitacion mayor'
    return 'Realsa Brokers', 'proceso menor o sin ponderacion fuerte de experiencia'

# ------------------------------------------------------------------- pipeline
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--min-rm', type=float, default=500)
    ap.add_argument('--min-nacional', type=float, default=2000)
    ap.add_argument('--min-dias', type=int, default=1)
    ap.add_argument('--max-detalles', type=int, default=400)
    ap.add_argument('--pausa', type=float, default=1.1)
    ap.add_argument('--presupuesto', type=int, default=None, help='segundos maximos de fetch por tanda')
    a = ap.parse_args()

    os.makedirs(DATA, exist_ok=True)
    uf, uf_fecha = uf_hoy(); log(f"UF {uf:,.2f} ({uf_fecha})")

    L = listado_activas(); log(f"licitaciones activas: {len(L)}")
    cand = [x for x in L if prefiltro(x.get('Nombre',''))]
    log(f"pasan prefiltro de titulo: {len(cand)}")
    cand = cand[:a.max_detalles]

    cache = detalles([x['CodigoExterno'] for x in cand], cargar(CACHE, {}), a.pausa, a.presupuesto)

    filas, descartes = [], []
    for x in cand:
        cod = x['CodigoExterno']; det = cache.get(cod) or {}
        if not det: continue
        items = (det.get('Items') or {}).get('Listado') or []
        score, motivos, desc = puntuar(det.get('Nombre'), det.get('Descripcion'), items)
        comp = det.get('Comprador') or {}
        region = comp.get('RegionUnidad') or ''
        ufv, monto_txt = monto_uf(det, uf)
        if desc or score < UMBRAL_MATCH:
            descartes.append({'codigo': cod, 'nombre': det.get('Nombre'), 'score': score,
                              'motivo': desc or f"score {score} < {UMBRAL_MATCH}"}); continue
        pasa, umbral_txt = aplica_umbral(ufv, region, a.min_rm, a.min_nacional)
        dias = det.get('DiasCierreLicitacion')
        dias = int(dias) if str(dias).strip().lstrip('-').isdigit() else None
        bajo = None
        if not pasa: bajo = f"bajo umbral de monto ({umbral_txt})"
        elif dias is not None and dias < a.min_dias: bajo = f"cierra en {dias} dias"

        ent, razon_ent = asignar_entidad(det, ufv, score)
        rango = RANGO_TIPO.get((det.get('Tipo') or '').upper())
        tipo_op, accion = clasificar_oportunidad(det.get('Nombre'), det.get('Descripcion'),
                                                 [i.get('CodigoCategoria') for i in items])
        f = (det.get('Fechas') or {})
        filas.append({
            'Codigo': cod, 'Nombre': det.get('Nombre'), 'Score': score,
            'Prioridad': 'ALTA' if score >= UMBRAL_ALTO else 'MEDIA',
            'Tipo de oportunidad': tipo_op, 'Accion sugerida': accion,
            'Entidad sugerida': ent, 'Razon entidad': razon_ent,
            'Organismo': comp.get('NombreOrganismo'), 'Unidad': comp.get('NombreUnidad'),
            'Region': (region or '').strip(), 'Comuna': comp.get('ComunaUnidad'),
            'Tipo': det.get('Tipo'), 'Estado': det.get('Estado'),
            'Monto publicado': monto_txt, 'Monto UF': round(ufv, 0) if ufv else None,
            'Dias al cierre': dias,
            'Cierre': (f.get('FechaCierre') or det.get('FechaCierre') or '')[:16].replace('T',' '),
            'Publicacion': (f.get('FechaPublicacion') or '')[:10],
            'Descripcion': (det.get('Descripcion') or '').replace('\r',' ').replace('\n',' ')[:900],
            'Por que calza': ' | '.join(motivos[:5]),
            'Rango estimado por tipo': rango or '',
            'Bajo umbral': bajo or '',
            'Contacto': det.get('NombreResponsableContrato') or '',
            'Email contacto': det.get('EmailResponsableContrato') or '',
            'URL': f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={cod}",
        })

    bajo_umbral = [r for r in filas if r['Bajo umbral']]
    filas = [r for r in filas if not r['Bajo umbral']]
    filas.sort(key=lambda r: (-r['Score'], r['Dias al cierre'] if r['Dias al cierre'] is not None else 999))
    bajo_umbral.sort(key=lambda r: -r['Score'])
    out = {'generado': dt.datetime.now().isoformat(timespec='seconds'), 'uf': uf,
           'activas': len(L), 'candidatos': len(cand), 'matches': len(filas),
           'parametros': vars(a), 'filas': filas, 'bajo_umbral': bajo_umbral, 'descartes': descartes}
    json.dump(out, open(os.path.join(DATA, 'ultima_corrida.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    log(f"MATCHES: {len(filas)}  |  bajo umbral: {len(bajo_umbral)}  |  descartes: {len(descartes)}")
    for r in filas[:15]:
        log(f"  {r['Score']:>3} {r['Entidad sugerida'][:6]:<6} {r['Region'][:22]:<22} {r['Nombre'][:70]}")

if __name__ == '__main__':
    main()
