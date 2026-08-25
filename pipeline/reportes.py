# -*- coding: utf-8 -*-
"""Genera Excel con historico, resumen ejecutivo y dashboard HTML."""
import json, os, datetime as dt, html
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get('MP_DATA') or os.path.join(BASE,'data')
HIST = os.path.join(DATA,'historico.json')
AZUL='1F3B57'; GRIS='F2F4F6'; VERDE='1E7A4B'; AMBAR='B7791F'; ROJO='A32626'
ARIAL = 'Arial'

def cargar(p, d):
    if os.path.exists(p):
        try: return json.load(open(p, encoding='utf-8'))
        except Exception: return d
    return d

# ------------------------------------------------------------------ historico
def actualizar_historico(filas, hoy):
    h = cargar(HIST, {})
    vistos = set()
    for r in filas:
        c = r['Codigo']; vistos.add(c)
        prev = h.get(c)
        if not prev:
            r['Novedad'] = 'NUEVA'
            h[c] = {'primera_vista': hoy, 'ultima_vista': hoy, 'score': r['Score'],
                    'estado': r['Estado'], 'cierre': r['Cierre'], 'monto_uf': r['Monto UF'],
                    'nombre': r['Nombre'], 'entidad': r['Entidad sugerida']}
        else:
            cambios = []
            if prev.get('estado') != r['Estado']: cambios.append(f"estado {prev.get('estado')}->{r['Estado']}")
            if prev.get('cierre') != r['Cierre']: cambios.append(f"cierre {prev.get('cierre')}->{r['Cierre']}")
            if prev.get('monto_uf') != r['Monto UF']: cambios.append(f"monto UF {prev.get('monto_uf')}->{r['Monto UF']}")
            r['Novedad'] = ('CAMBIO: ' + '; '.join(cambios)) if cambios else 'VIGENTE'
            prev.update({'ultima_vista': hoy, 'score': r['Score'], 'estado': r['Estado'],
                         'cierre': r['Cierre'], 'monto_uf': r['Monto UF']})
    cerradas = [{'Codigo':c, **v} for c,v in h.items() if c not in vistos and v.get('ultima_vista')!=hoy]
    json.dump(h, open(HIST,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
    return h, cerradas

# ---------------------------------------------------------------------- excel
COLS = ['Nueva','Novedad','Prioridad','Score','Tipo de oportunidad','Accion sugerida','Entidad sugerida','Nombre','Organismo','Region',
        'Tipo','Monto publicado','Monto UF','Dias al cierre','Cierre','Codigo',
        'Por que calza','Razon entidad','Descripcion','Contacto','Email contacto','URL']
ANCHOS = {'Nueva':9,'Novedad':16,'Tipo de oportunidad':22,'Accion sugerida':52,'Prioridad':10,'Score':7,'Entidad sugerida':16,'Nombre':52,'Organismo':34,
          'Region':24,'Tipo':6,'Monto publicado':18,'Monto UF':12,'Dias al cierre':13,
          'Cierre':17,'Codigo':18,'Por que calza':46,'Razon entidad':38,'Descripcion':60,
          'Contacto':22,'Email contacto':26,'URL':30}

def encabezado(ws, cols, fila=1):
    thin = Side(style='thin', color='D0D5DA')
    for j,c in enumerate(cols,1):
        cel = ws.cell(fila,j,c)
        cel.font = Font(name=ARIAL, bold=True, color='FFFFFF', size=10)
        cel.fill = PatternFill('solid', fgColor=AZUL)
        cel.alignment = Alignment(vertical='center', wrap_text=True)
        cel.border = Border(bottom=thin)
        ws.column_dimensions[get_column_letter(j)].width = ANCHOS.get(c, 18)
    ws.row_dimensions[fila].height = 30
    ws.freeze_panes = ws.cell(fila+1,1)

def excel(corrida, filas, cerradas, ruta, bajo=None):
    wb = Workbook(); thin = Side(style='thin', color='E3E7EA')

    def L(nombre):
        """Letra de columna de la hoja Matches. Evita que agregar una columna
        rompa silenciosamente las formulas del Resumen."""
        return get_column_letter(COLS.index(nombre) + 1)

    ws = wb.active; ws.title = 'Resumen'
    ws['A1'] = 'Observatorio de licitaciones — Mercado Publico'
    ws['A1'].font = Font(name=ARIAL, bold=True, size=15, color=AZUL)
    ws['A2'] = f"Corrida {corrida['generado'][:16].replace('T',' ')} · UF {corrida['uf']:,.2f} · " \
               f"{corrida['activas']:,} licitaciones activas barridas"
    ws['A2'].font = Font(name=ARIAL, size=10, color='5A6572')
    filas_n = len(filas)
    metricas = [
        ('Matches totales', f'=COUNTA(Matches!{L("Codigo")}2:{L("Codigo")}{filas_n+1})'),
        ('NUEVAS esta corrida', f'=COUNTIF(Matches!{L("Nueva")}2:{L("Nueva")}{filas_n+1},"SI")'),
        ('Con cambios', f'=COUNTIF(Matches!{L("Novedad")}2:{L("Novedad")}{filas_n+1},"CAMBIO*")'),
        ('Prioridad ALTA', f'=COUNTIF(Matches!{L("Prioridad")}2:{L("Prioridad")}{filas_n+1},"ALTA")'),
        ('Mandatos de servicio', f'=COUNTIF(Matches!{L("Tipo de oportunidad")}2:{L("Tipo de oportunidad")}{filas_n+1},"Mandato de SERVICIO")'),
        ('Estado busca inmueble', f'=COUNTIF(Matches!{L("Tipo de oportunidad")}2:{L("Tipo de oportunidad")}{filas_n+1},"Estado BUSCA inmueble")'),
        ('Estado ofrece inmueble', f'=COUNTIF(Matches!{L("Tipo de oportunidad")}2:{L("Tipo de oportunidad")}{filas_n+1},"Estado OFRECE inmueble")'),
        ('Sugeridas a Gamma', f'=COUNTIF(Matches!{L("Entidad sugerida")}2:{L("Entidad sugerida")}{filas_n+1},"Gamma")'),
        ('Sugeridas a Realsa Brokers', f'=COUNTIF(Matches!{L("Entidad sugerida")}2:{L("Entidad sugerida")}{filas_n+1},"Realsa Brokers")'),
        ('Cierran en <= 7 dias', f'=COUNTIFS(Matches!{L("Dias al cierre")}2:{L("Dias al cierre")}{filas_n+1},"<=7",Matches!{L("Dias al cierre")}2:{L("Dias al cierre")}{filas_n+1},">=0")'),
        ('Monto UF agregado (publicado)', f'=SUM(Matches!{L("Monto UF")}2:{L("Monto UF")}{filas_n+1})'),
        ('Descartadas por reglas', corrida.get('descartes_n', len(corrida.get('descartes',[])))),
        ('Cerradas / salieron del radar', len(cerradas)),
    ]
    ws['A4']='Indicador'; ws['B4']='Valor'
    for c in ('A4','B4'):
        ws[c].font = Font(name=ARIAL, bold=True, color='FFFFFF'); ws[c].fill = PatternFill('solid', fgColor=AZUL)
    for i,(k,v) in enumerate(metricas, start=5):
        ws.cell(i,1,k).font = Font(name=ARIAL, size=10)
        cel = ws.cell(i,2,v); cel.font = Font(name=ARIAL, size=10, bold=True)
        cel.number_format = '#,##0'
        for cc in (ws.cell(i,1), cel): cc.border = Border(bottom=thin)
    ws.column_dimensions['A'].width = 34; ws.column_dimensions['B'].width = 18
    leyenda = ws.cell(len(metricas)+3,1,
        'Marca de novedad: la columna "Nueva" vale SI cuando la licitacion no aparecia en ninguna '
        'corrida anterior; toda la fila queda con fondo verde. Fondo ambar = la licitacion ya estaba '
        'en el radar pero cambio de estado, fecha de cierre o monto (el detalle va en la columna '
        '"Novedad"). La comparacion se hace contra la hoja Historico, que acumula todas las corridas.')
    leyenda.font = Font(name=ARIAL, size=9, italic=True, color='5A6572')
    leyenda.alignment = Alignment(wrap_text=True, vertical='top')
    ws.merge_cells(start_row=leyenda.row, start_column=1, end_row=leyenda.row+2, end_column=8)

    nota = ws.cell(len(metricas)+8,1,
        'Umbrales aplicados: Region Metropolitana desde UF %s · resto del pais desde UF %s · '
        'minimo %s dias al cierre. Las licitaciones sin monto publicado NO se descartan: pasan '
        'marcadas como "no publicado" (Mercado Publico permite ocultar el monto estimado). '
        'Fuente: API oficial api.mercadopublico.cl. Valor UF: mindicador.cl.'
        % (corrida['parametros']['min_rm'], corrida['parametros']['min_nacional'],
           corrida['parametros']['min_dias']))
    nota.font = Font(name=ARIAL, size=9, italic=True, color='5A6572')
    nota.alignment = Alignment(wrap_text=True, vertical='top')
    ws.merge_cells(start_row=nota.row, start_column=1, end_row=nota.row+3, end_column=8)

    ws = wb.create_sheet('Matches'); encabezado(ws, COLS)
    VERDE_FILA = PatternFill('solid', fgColor='E8F6EE')   # fila completa: licitacion nueva
    AMBAR_FILA = PatternFill('solid', fgColor='FFF8E6')   # fila completa: cambio detectado
    for i,r in enumerate(filas, start=2):
        es_nueva = r.get('Novedad') == 'NUEVA'
        es_cambio = str(r.get('Novedad','')).startswith('CAMBIO')
        r['Nueva'] = 'SI' if es_nueva else 'NO'
        for j,c in enumerate(COLS,1):
            v = r.get(c)
            cel = ws.cell(i,j,v)
            cel.font = Font(name=ARIAL, size=10)
            cel.alignment = Alignment(vertical='top', wrap_text=c in ('Nombre','Descripcion','Por que calza','Razon entidad','Organismo','Accion sugerida'))
            cel.border = Border(bottom=thin)
            if es_nueva: cel.fill = VERDE_FILA
            elif es_cambio: cel.fill = AMBAR_FILA
            if c=='Nueva':
                cel.font = Font(name=ARIAL, size=11, bold=True, color=VERDE if es_nueva else '9AA5B1')
                cel.alignment = Alignment(horizontal='center', vertical='center')
            if c=='Prioridad':
                cel.font = Font(name=ARIAL, size=10, bold=True, color=ROJO if v=='ALTA' else AMBAR)
            if c=='Novedad' and v and v.startswith(('NUEVA','CAMBIO')):
                cel.fill = PatternFill('solid', fgColor='FFF4D6' if v.startswith('CAMBIO') else 'DCF2E4')
                cel.font = Font(name=ARIAL, size=10, bold=True, color=AMBAR if v.startswith('CAMBIO') else VERDE)
            if c=='URL' and v:
                cel.value='Ver ficha'; cel.hyperlink=v; cel.font=Font(name=ARIAL,size=10,color='0563C1',underline='single')
            if c=='Monto UF' and v: cel.number_format='#,##0'
        ws.row_dimensions[i].height = 46
    if filas: ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{len(filas)+1}"

    ws = wb.create_sheet('Historico')
    hcols = ['Codigo','Nombre','Entidad','Score','Estado','Cierre','Monto UF','Primera vista','Ultima vista','Semanas en radar']
    encabezado(ws, hcols)
    h = cargar(HIST, {}); hoy = dt.date.today()
    for i,(cod,v) in enumerate(sorted(h.items(), key=lambda kv:-kv[1].get('score',0)), start=2):
        try: sem = max(1, ((hoy - dt.date.fromisoformat(v['primera_vista'][:10])).days)//7 + 1)
        except Exception: sem = 1
        vals = [cod, v.get('nombre'), v.get('entidad'), v.get('score'), v.get('estado'),
                v.get('cierre'), v.get('monto_uf'), v.get('primera_vista')[:10],
                v.get('ultima_vista')[:10], sem]
        for j,val in enumerate(vals,1):
            cel = ws.cell(i,j,val); cel.font=Font(name=ARIAL,size=10)
            cel.alignment=Alignment(vertical='top', wrap_text=(j==2)); cel.border=Border(bottom=thin)
        ws.column_dimensions['B'].width=52

    bajo = bajo or []
    ws = wb.create_sheet('Bajo umbral')
    bcols = ['Score','Nombre','Organismo','Region','Tipo','Monto publicado','Monto UF',
             'Rango estimado por tipo','Cierre','Por que no entro','Codigo','URL']
    ANCHOS.update({'Rango estimado por tipo':30,'Por que no entro':38})
    encabezado(ws, bcols)
    for i,r in enumerate(bajo, start=2):
        vals=[r['Score'],r['Nombre'],r['Organismo'],r['Region'],r['Tipo'],r['Monto publicado'],
              r['Monto UF'],r.get('Rango estimado por tipo'),r['Cierre'],r['Bajo umbral'],r['Codigo'],r['URL']]
        for j,v in enumerate(vals,1):
            cel=ws.cell(i,j,v); cel.font=Font(name=ARIAL,size=10)
            cel.alignment=Alignment(vertical='top', wrap_text=j in (2,3,10)); cel.border=Border(bottom=thin)
            if j==12 and v: cel.value='Ver ficha'; cel.hyperlink=v; cel.font=Font(name=ARIAL,size=10,color='0563C1',underline='single')
        ws.row_dimensions[i].height=42
    ws.cell(len(bajo)+3,1,'Estas licitaciones SI calzan con el servicio, pero quedan fuera por monto o plazo. '
            'Ojo: Mercado Publico publica el valor del CONTRATO (honorario), no el valor del activo — '
            'una tasacion de un edificio grande puede aparecer como UF 73. Revisar antes de descartar.'
            ).font = Font(name=ARIAL, size=9, italic=True, color='5A6572')

    ws = wb.create_sheet('Descartes (auditoria)')
    encabezado(ws, ['Codigo','Nombre','Score','Motivo del descarte'])
    for i,d in enumerate(corrida.get('descartes',[]), start=2):
        for j,val in enumerate([d['codigo'], d['nombre'], d['score'], d['motivo']],1):
            cel=ws.cell(i,j,val); cel.font=Font(name=ARIAL,size=10)
            cel.alignment=Alignment(vertical='top', wrap_text=(j in (2,4))); cel.border=Border(bottom=thin)
    for col,w in zip('ABCD',[18,60,8,46]): ws.column_dimensions[col].width=w

    wb.calculation.fullCalcOnLoad = True  # Excel recalcula al abrir
    wb.save(ruta); return ruta

# ------------------------------------------------------------------- markdown
def resumen_md(corrida, filas, cerradas, ruta):
    hoy = dt.datetime.now()
    altas = [r for r in filas if r['Prioridad']=='ALTA']
    nuevas = [r for r in filas if r.get('Novedad')=='NUEVA']
    urgentes = [r for r in filas if r['Dias al cierre'] is not None and r['Dias al cierre']<=7]
    L=[]
    L.append(f"# Licitaciones que calzan — Gamma / Realsa Brokers\n")
    L.append(f"**Corrida:** {hoy:%d-%m-%Y %H:%M} · **UF:** {corrida['uf']:,.2f} · "
             f"**Universo barrido:** {corrida['activas']:,} licitaciones activas en Mercado Publico\n")
    L.append(f"**{len(filas)} matches** ({len(altas)} prioridad alta, {len(nuevas)} nuevas). "
             f"{len(urgentes)} cierran dentro de 7 dias.\n")
    if urgentes:
        L.append("## Accionables esta semana (cierre <= 7 dias)\n")
        for r in sorted(urgentes, key=lambda x:x['Dias al cierre']):
            L.append(f"- **{r['Dias al cierre']}d** · `{r['Codigo']}` · **{r['Nombre'][:110]}** — "
                     f"{r['Organismo']} ({r['Region']}). {r['Monto publicado']}. "
                     f"→ *{r['Entidad sugerida']}*. [Ficha]({r['URL']})")
        L.append("")
    L.append("## Prioridad alta\n")
    if not altas: L.append("_Sin licitaciones de prioridad alta en esta corrida._\n")
    for r in altas[:20]:
        L.append(f"### {r['Nombre'][:130]}")
        L.append(f"`{r['Codigo']}` · {r['Organismo']} · {r['Region']} · {r['Tipo']} · "
                 f"cierra {r['Cierre']} ({r['Dias al cierre']} dias) · {r['Monto publicado']}")
        L.append(f"**Tipo de oportunidad:** {r['Tipo de oportunidad']} — {r['Accion sugerida']}  \n"
                 f"**Entidad sugerida:** {r['Entidad sugerida']} — {r['Razon entidad']}  ")
        L.append(f"**Por que calza (score {r['Score']}):** {r['Por que calza']}  ")
        L.append(f"{r['Descripcion'][:400]}  ")
        L.append(f"[Ver en Mercado Publico]({r['URL']})\n")
    medias = [r for r in filas if r['Prioridad']=='MEDIA']
    if medias:
        L.append("## Prioridad media — revisar por excepcion\n")
        L.append("| Score | Licitacion | Organismo | Region | Cierre | Monto | Entidad |")
        L.append("|---|---|---|---|---|---|---|")
        for r in medias[:40]:
            L.append(f"| {r['Score']} | [{r['Nombre'][:70]}]({r['URL']}) | {str(r['Organismo'])[:35]} | "
                     f"{r['Region'][:20]} | {r['Cierre'][:10]} | {r['Monto publicado']} | {r['Entidad sugerida']} |")
        L.append("")
    if cerradas:
        L.append("## Salieron del radar desde la ultima corrida\n")
        for c in cerradas[:15]:
            L.append(f"- `{c['Codigo']}` {str(c.get('nombre'))[:90]} (vista por ultima vez {c.get('ultima_vista','')[:10]})")
        L.append("")
    L.append("---\n")
    L.append(f"_Metodo: barrido del endpoint oficial `licitaciones.json?estado=activas` de "
             f"api.mercadopublico.cl; prefiltro por titulo; detalle completo (descripcion, comprador, "
             f"items UNSPSC, monto) de {corrida['candidatos']} candidatos; scoring por taxonomia de "
             f"servicios inmobiliarios. Umbrales: RM desde UF {corrida['parametros']['min_rm']}, "
             f"resto del pais desde UF {corrida['parametros']['min_nacional']}. "
             f"{len(corrida.get('descartes',[]))} descartes quedan auditables en la hoja "
             f"'Descartes' del Excel._")
    open(ruta,'w',encoding='utf-8').write('\n'.join(L)); return ruta
