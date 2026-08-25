# -*- coding: utf-8 -*-
"""Dashboard HTML autocontenido de licitaciones que calzan."""
import json, html, datetime as dt

TPL = """<title>Radar de Licitaciones</title>
<style>
:root{--bg:#f7f8f9;--surface:#fff;--ink:#111820;--muted:#5d6b7a;--line:#e2e6ea;
--brand:#1f3b57;--alta:#a32626;--media:#b7791f;--ok:#1e7a4b;--chip:#eef1f4;}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
--bg:#0e1318;--surface:#161c23;--ink:#e8edf2;--muted:#94a3b3;--line:#26303a;
--brand:#7fb3e0;--alta:#ff8080;--media:#e8b44a;--ok:#5fd39b;--chip:#1e262f;}}
:root[data-theme="dark"]{--bg:#0e1318;--surface:#161c23;--ink:#e8edf2;--muted:#94a3b3;
--line:#26303a;--brand:#7fb3e0;--alta:#ff8080;--media:#e8b44a;--ok:#5fd39b;--chip:#1e262f;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;padding:28px 20px 60px}
.wrap{max-width:1180px;margin:0 auto}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.02em}
.sub{color:var(--muted);font-size:13.5px;margin-bottom:22px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:24px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.kpi.nuevo{border-color:var(--ok);background:linear-gradient(0deg,rgba(30,122,75,.07),rgba(30,122,75,.07))}
.kpi.nuevo b{color:var(--ok)}
.kpi b{display:block;font-size:26px;line-height:1.1;letter-spacing:-.02em}
.kpi span{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.05em}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px;align-items:center}
button.f{background:var(--chip);border:1px solid var(--line);color:var(--ink);border-radius:99px;
padding:6px 14px;font-size:13px;cursor:pointer}
button.f[aria-pressed="true"]{background:var(--brand);color:#fff;border-color:var(--brand)}
.card{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--media);
border-radius:10px;padding:16px 18px;margin-bottom:12px;position:relative}
.card.alta{border-left-color:var(--alta)}
.card.nueva{border-left-width:8px;border-left-color:var(--ok);
box-shadow:0 0 0 1px var(--ok) inset,0 2px 10px rgba(30,122,75,.10)}
.card.nueva::after{content:"NUEVA";position:absolute;top:14px;right:16px;background:var(--ok);
color:#fff;font-size:10.5px;font-weight:700;letter-spacing:.09em;padding:3px 9px;border-radius:4px}
.card.nueva h3{padding-right:78px}
.card.cambio{border-left-width:8px;border-left-color:var(--media)}
.card h3{margin:0 0 6px;font-size:16.5px;line-height:1.35}
.card h3 a{color:inherit;text-decoration:none}.card h3 a:hover{text-decoration:underline}
.meta{color:var(--muted);font-size:12.5px;margin-bottom:10px}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.tag{background:var(--chip);border-radius:5px;padding:2px 9px;font-size:11.5px;color:var(--muted)}
.tag.p{color:#fff;background:var(--media);font-weight:600}.tag.p.alta{background:var(--alta)}
.tag.n{background:var(--ok);color:#fff;font-weight:600}
.tag.d{background:var(--alta);color:#fff;font-weight:600}
.desc{font-size:13.5px;color:var(--muted);margin:0 0 8px}
.why{font-size:12px;color:var(--muted);font-family:ui-monospace,Menlo,monospace;
background:var(--chip);padding:7px 10px;border-radius:6px;overflow-x:auto;white-space:nowrap}
h2{font-size:15px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);
margin:32px 0 12px;border-top:1px solid var(--line);padding-top:18px}
table{width:100%;border-collapse:collapse;font-size:13px}
.tw{overflow-x:auto}
th{text-align:left;color:var(--muted);font-weight:600;font-size:11.5px;text-transform:uppercase;
letter-spacing:.04em;padding:8px 10px;border-bottom:1px solid var(--line)}
td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
td a{color:var(--brand)}
.foot{color:var(--muted);font-size:12px;margin-top:34px;border-top:1px solid var(--line);padding-top:14px}
</style>
<div class="wrap">
<h1>Radar de licitaciones — Gamma / Realsa Brokers</h1>
<div class="sub">__SUB__</div>
<div class="kpis">__KPIS__</div>
<div class="bar"><strong style="font-size:13px;margin-right:4px">Filtrar:</strong>__FILTROS__</div>
<div id="cards">__CARDS__</div>
__BAJO__
<div class="foot">__FOOT__</div>
</div>
<script>
document.querySelectorAll('button.f').forEach(b=>b.onclick=()=>{
  const g=b.dataset.g, on=b.getAttribute('aria-pressed')==='true';
  document.querySelectorAll(`button.f[data-g="${g}"]`).forEach(o=>o.setAttribute('aria-pressed','false'));
  b.setAttribute('aria-pressed', on?'false':'true');
  const act={};
  document.querySelectorAll('button.f[aria-pressed="true"]').forEach(o=>act[o.dataset.g]=o.dataset.v);
  document.querySelectorAll('#cards .card').forEach(c=>{
    c.style.display=Object.entries(act).every(([g,v])=>c.dataset[g]===v)?'':'none';});
});
</script>"""

def esc(x): return html.escape(str(x or ''))


def num(v, dec=0):
    """Formato chileno: miles con punto, decimales con coma."""
    txt = f"{v:,.{dec}f}"
    return txt.replace(',', '\x00').replace('.', ',').replace('\x00', '.')

def build(corrida, filas, bajo, ruta):
    altas=[r for r in filas if r['Prioridad']=='ALTA']
    nuevas=[r for r in filas if r.get('Novedad')=='NUEVA']
    urg=[r for r in filas if r['Dias al cierre'] is not None and r['Dias al cierre']<=7]
    kpis=[(len(filas),'Matches vigentes'),(len(altas),'Prioridad alta'),(len(nuevas),'Nuevas'),
          (len(urg),'Cierran ≤ 7 días'),(num(corrida['activas']),'Universo barrido')]
    K=''.join(f'<div class="kpi{" nuevo" if k=="Nuevas" and int(v)>0 else ""}"><b>{v}</b><span>{k}</span></div>'
              for v,k in kpis)

    regs=sorted({r['Region'] for r in filas if r['Region']})
    F=(f'<button class="f" data-g="nue" data-v="si" aria-pressed="false" '
       f'style="border-color:var(--ok);color:var(--ok);font-weight:600">Solo nuevas ({len(nuevas)})</button>')
    F+=''.join(f'<button class="f" data-g="ent" data-v="{esc(e)}" aria-pressed="false">{esc(e)}</button>'
              for e in ('Gamma','Realsa Brokers'))
    F+=''.join(f'<button class="f" data-g="op" data-v="{esc(o)}" aria-pressed="false">{esc(o)}</button>'
              for o in ('Mandato de SERVICIO','Estado BUSCA inmueble','Estado OFRECE inmueble'))
    F+=''.join(f'<button class="f" data-g="pri" data-v="{p}" aria-pressed="false">{p}</button>' for p in ('ALTA','MEDIA'))
    F+=''.join(f'<button class="f" data-g="reg" data-v="{esc(r)}" aria-pressed="false">{esc(r).replace("Región ","")}</button>' for r in regs)

    C=[]
    for r in filas:
        d=r['Dias al cierre']
        tags=[f'<span class="tag p {"alta" if r["Prioridad"]=="ALTA" else ""}">{r["Prioridad"]} · {r["Score"]}</span>',
              f'<span class="tag" style="background:var(--brand);color:#fff">{esc(r["Tipo de oportunidad"])}</span>',
              f'<span class="tag">{esc(r["Entidad sugerida"])}</span>',
              f'<span class="tag">{esc(r["Tipo"])} · {esc(r["Monto publicado"])}</span>']
        if d is not None and d<=7: tags.insert(1,f'<span class="tag d">cierra en {d} d</span>')
        if str(r.get('Novedad','')).startswith('CAMBIO'):
            tags.insert(1, f'<span class="tag n" style="background:var(--media)">{esc(r["Novedad"][:44])}</span>')
        es_nueva = r.get('Novedad')=='NUEVA'
        es_cambio = str(r.get('Novedad','')).startswith('CAMBIO')
        clases = ' '.join(filter(None, ['card', 'alta' if r['Prioridad']=='ALTA' else '',
                                        'nueva' if es_nueva else '', 'cambio' if es_cambio else '']))
        C.append(f'''<div class="{clases}" data-nue="{'si' if es_nueva else 'no'}"
 data-op="{esc(r['Tipo de oportunidad'])}" data-ent="{esc(r['Entidad sugerida'])}" data-pri="{r['Prioridad']}" data-reg="{esc(r['Region'])}">
<h3><a href="{esc(r['URL'])}" target="_blank" rel="noopener">{esc(r['Nombre'])}</a></h3>
<div class="meta">{esc(r['Organismo'])} · {esc(r['Region'])} · cierra {esc(r['Cierre'])}
 · <code>{esc(r['Codigo'])}</code></div>
<div class="tags">{''.join(tags)}</div>
<p class="desc"><strong>Acción:</strong> {esc(r['Accion sugerida'])}</p>
<p class="desc">{esc(r['Descripcion'][:300])}</p>
<div class="why">{esc(r['Por que calza'])}</div></div>''')

    B=''
    if bajo:
        rows=''.join(f"<tr><td>{r['Score']}</td><td><a href=\"{esc(r['URL'])}\" target=\"_blank\">{esc(r['Nombre'][:80])}</a></td>"
                     f"<td>{esc(r['Organismo'])[:38]}</td><td>{esc(r['Region']).replace('Región ','')}</td>"
                     f"<td>{esc(r['Monto publicado'])}</td><td>{esc(r['Bajo umbral'])}</td></tr>" for r in bajo)
        B=(f'<h2>Bajo umbral — calzan con el servicio pero no pasan los filtros de monto o plazo</h2>'
           f'<div class="tw"><table><tr><th>Score</th><th>Licitación</th><th>Organismo</th><th>Región</th>'
           f'<th>Monto</th><th>Por qué no entró</th></tr>{rows}</table></div>')

    sub=(f"Corrida {corrida['generado'][:16].replace('T',' ')} · UF {num(corrida['uf'],2)} · "
         f"{corrida['candidatos']} candidatos analizados en detalle sobre "
         f"{num(corrida['activas'])} licitaciones activas")
    foot=("<strong>Marca de novedad:</strong> se considera NUEVA la licitación que no aparecía en "
          "ninguna corrida anterior — la comparación es contra el histórico acumulado, no contra la "
          "fecha de publicación del aviso. Las tarjetas con banda ámbar ya estaban en el radar pero "
          "cambiaron de estado, fecha de cierre o monto.<br><br>"
          "Fuente: API oficial <code>api.mercadopublico.cl</code> (endpoint licitaciones activas) + valor UF de mindicador.cl. "
          f"Umbrales: RM desde UF {num(corrida['parametros']['min_rm'])}, resto del país desde UF "
          f"{num(corrida['parametros']['min_nacional'])}, "
          f"mínimo {corrida['parametros']['min_dias']} día(s) al cierre. Las licitaciones sin monto publicado no se descartan. "
          "El score combina términos núcleo del negocio inmobiliario, objeto de la licitación y categoría UNSPSC del ítem.")
    out=(TPL.replace('__SUB__',sub).replace('__KPIS__',K).replace('__FILTROS__',F)
            .replace('__CARDS__',''.join(C) or '<p class="desc">Sin matches en esta corrida.</p>')
            .replace('__BAJO__',B).replace('__FOOT__',foot))
    open(ruta,'w',encoding='utf-8').write(out); return ruta
