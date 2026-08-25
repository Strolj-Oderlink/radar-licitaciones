# -*- coding: utf-8 -*-
"""Taxonomia de matching Gamma / Realsa Brokers vs Mercado Publico."""
import re, unicodedata

def norm(s):
    if not s: return ""
    s = unicodedata.normalize('NFD', str(s).lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s)

# ---------------------------------------------------------------- NUCLEO
# Terminos que por si solos describen el servicio que venden Gamma / Realsa.
NUCLEO = {
    'corretaje': 26, 'corredor de propiedades': 26, 'corredora de propiedades': 26,
    'intermediacion inmobiliaria': 26, 'asesoria inmobiliaria': 24,
    'servicios inmobiliarios': 24, 'gestion inmobiliaria': 22,
    'tasacion': 24, 'tasaciones': 24, 'tasar': 20, 'peritaje de inmueble': 24,
    'valorizacion de inmueble': 24, 'valorizacion de activos': 22,
    'valoracion de inmueble': 24, 'informe de tasacion': 26,
    'due diligence inmobiliari': 26, 'estudio de titulos': 18,
    'busqueda de inmueble': 24, 'busqueda de propiedad': 24,
    'gestion de activos inmobiliarios': 26, 'administracion de cartera de inmuebles': 24,
    'plan maestro': 16, 'estudio de mercado inmobiliario': 24,
    'factibilidad inmobiliaria': 22, 'catastro de inmuebles': 20,
    'regularizacion de propiedades': 16, 'saneamiento de titulos': 16,
    'enajenacion de inmueble': 24, 'enajenacion de bienes raices': 26,
    'venta de inmueble': 22, 'remate de inmueble': 18,
    'adquisicion de inmueble': 22, 'compra de inmueble': 22,
    'compra de propiedad': 22, 'adquisicion de propiedad': 22,
    'expropiacion': 14, 'concesion onerosa': 16, 'uso oneroso': 14,
}

# Objeto inmobiliario: da contexto a verbos ambiguos como "arriendo".
OBJETO = {
    'inmueble': 14, 'inmuebles': 14, 'bien raiz': 16, 'bienes raices': 16,
    'bien nacional': 10, 'propiedad fiscal': 14, 'inmueble fiscal': 16,
    'oficina': 10, 'oficinas': 10, 'dependencias': 8, 'sede': 8,
    'edificio': 8, 'edificacion': 8, 'local comercial': 10, 'locales comerciales': 10,
    'bodega': 7, 'bodegas': 7, 'galpon': 7, 'terreno': 9, 'terrenos': 9,
    'sitio eriazo': 12, 'paño': 6, 'estacionamiento': 5, 'estacionamientos': 5,
    'casa': 5, 'departamento': 5, 'recinto': 5, 'inmobiliario': 10, 'inmobiliaria': 10,
}

# Verbos de transaccion: solo puntuan si hay OBJETO inmobiliario en el texto.
VERBO_CONTEXTUAL = {
    'arriendo': 12, 'arrendamiento': 12, 'arrendar': 12, 'subarriendo': 10,
    'canon de arrendamiento': 14, 'contrato de arriendo': 14,
    'leasing': 8, 'comodato': 8, 'permuta': 10, 'venta': 6, 'compraventa': 12,
    'habilitacion': 6, 'traslado': 4, 'mudanza': 5,
}

# ------------------------------------------------------- EXCLUSIONES DURAS
# Si aparecen en el NOMBRE, la licitacion se descarta aunque tenga "arriendo".
EXCLUYENTES = [
    'vehiculo','vehiculos','camion','camiones','camioneta','automovil','buses','bus ',
    'furgon','maquinaria','retroexcavadora','barredora','aljibe','gravilla','minibus',
    'embarcacion','lancha','nave','aeronave','helicoptero','grua',
    'impresora','impresoras','fotocopiadora','multifuncional','servidor','servidores',
    'data center','notebook','computador','computacional','software','licencia',
    'toner','equipo medico','equipos medicos','ecografo','tomografo','ventilador',
    'litotricia','laser','rayos x','resonancia','dialisis','ambulancia',
    'baño quimico','baños quimicos','contenedor','container','carpa','toldo',
    'andamio','generador','grupo electrogeno','aire acondicionado','ascensor',
    'casino','alimentacion','colacion','banqueteria','catering',
    'aseo','sanitizacion','desratizacion','jardineria','vigilancia','guardia',
    'seguridad privada','transporte de personal','flete','combustible','gas licuado',
    'utiles de oficina','articulos de oficina','mobiliario','muebles','sillas',
    'papeleria','libreria','insumos','materiales de construccion','vestuario',
    'capacitacion','seguro','poliza','internet','telefonia','celular','radio',
    'estudio de suelo','topografia','sondaje','pavimentacion','luminaria',
]

# ------------------------------------------------------------ CATEGORIAS UNSPSC
# 8013 = Servicios de bienes raices / inmobiliarios (senal mas fuerte del catalogo)
CAT_PREFIX = {
    '8013': 40,   # servicios inmobiliarios: arriendo, venta, administracion, tasacion
    '801016': 12, # consultoria de gestion
    '801015': 12, # consultoria de negocios
    '801116': 6,  # servicios de gestion de proyectos
    '9313': 8,    # analisis economico / estudios
}
CAT_TEXTO = {
    'bienes raices': 30, 'bienes raíces': 30, 'inmobiliari': 26,
    'tasacion': 26, 'tasación': 26, 'arrendamiento de propiedades': 30,
    'venta de edificios': 30, 'administracion de propiedades': 24,
}

UMBRAL_MATCH = 30          # score minimo para reportar
UMBRAL_ALTO  = 55          # score de prioridad alta


def excluido(titulo):
    """Exclusion dura sobre el titulo, con limites de palabra y salvoconducto
    para titulos que contienen un termino nucleo del negocio."""
    n = norm(titulo)
    if any(k in n for k in NUCLEO):
        return None
    for x in EXCLUYENTES:
        if re.search(r'\b' + re.escape(x.strip()) + r'e?s?\b', n):
            return x.strip()
    return None


def puntuar(nombre, descripcion, items):
    """Devuelve (score, motivos[], descartado_por|None)."""
    n_nom = norm(nombre)
    n_desc = norm(descripcion)
    texto = n_nom + ' ' + n_desc
    motivos, score = [], 0

    # Un termino nucleo en el titulo desactiva la exclusion dura: "TASACION DE BIENES
    # INMUEBLES Y MUEBLES" es negocio, no una compra de mobiliario.
    ex = excluido(nombre)
    if ex:
        return 0, [], f"exclusion dura en titulo: '{ex}'"

    hay_objeto = any(o in texto for o in OBJETO)

    for k, p in NUCLEO.items():
        if k in n_nom:
            score += p; motivos.append(f"nucleo/titulo: {k} (+{p})")
        elif k in n_desc:
            score += int(p * 0.6); motivos.append(f"nucleo/desc: {k} (+{int(p*0.6)})")

    for k, p in OBJETO.items():
        if re.search(r'\b'+re.escape(k), n_nom):
            score += p; motivos.append(f"objeto/titulo: {k} (+{p})"); break
    else:
        for k, p in OBJETO.items():
            if re.search(r'\b'+re.escape(k), n_desc):
                score += int(p*0.5); motivos.append(f"objeto/desc: {k} (+{int(p*0.5)})"); break

    if hay_objeto:
        for k, p in VERBO_CONTEXTUAL.items():
            if k in n_nom:
                score += p; motivos.append(f"transaccion: {k} (+{p})"); break
            if k in n_desc:
                score += int(p*0.5); motivos.append(f"transaccion/desc: {k} (+{int(p*0.5)})"); break

    cats = set()
    for it in (items or []):
        cod = str(it.get('CodigoCategoria') or it.get('CodigoProducto') or '')
        cat = norm(it.get('Categoria'))
        cats.add((cod, cat))
    mejor_cat = 0
    for cod, cat in cats:
        for pref, p in CAT_PREFIX.items():
            if cod.startswith(pref) and p > mejor_cat:
                mejor_cat = p; cat_motivo = f"UNSPSC {cod} (+{p})"
        for txt, p in CAT_TEXTO.items():
            if txt in cat and p > mejor_cat:
                mejor_cat = p; cat_motivo = f"categoria '{txt}' (+{p})"
    if mejor_cat:
        score += mejor_cat; motivos.append(cat_motivo)

    # Un solo objeto suelto ("oficina") sin nada mas no es un match.
    if score and not any(m.startswith(('nucleo', 'transaccion', 'UNSPSC', 'categoria')) for m in motivos):
        if mejor_cat == 0:
            return score, motivos, "solo mencion de inmueble, sin servicio inmobiliario"

    return min(score, 100), motivos, None


# ---------------------------------------------------------- TIPO DE OPORTUNIDAD
# Distinguir esto es lo que define la accion comercial: no es lo mismo que el
# Estado contrate un servicio de asesoria a que salga a buscar un inmueble.
def clasificar_oportunidad(nombre, descripcion, cats=()):
    t = norm(nombre) + ' ' + norm(descripcion)
    cats = ' '.join(str(c) for c in cats)

    ofrece = ('enajenacion','enajenar','venta de terreno','venta de inmueble','venta de propiedad',
              'venta de bienes raices','remate','licitacion publica de venta','concesion de local',
              'concesion onerosa','entrega en concesion','arrendamiento de inmueble fiscal',
              'venta de terrenos','disposicion de inmueble')
    if any(k in t for k in ofrece) or cats.startswith('801316'):
        return ('Estado OFRECE inmueble',
                'El organismo vende o concesiona un activo: oportunidad de representar comprador/'
                'operador o de asesorar el proceso. Revisar bases y valor minimo.')

    busca = ('arriendo','arrendamiento','arrendar','compra de inmueble','adquisicion de inmueble',
             'adquisicion de terreno','compra de terreno','compra de propiedad','busqueda de inmueble',
             'comodato de inmueble','se requiere inmueble','local para funcionamiento')
    servicio = ('tasacion','peritaje','valorizacion','avaluo','corretaje','asesoria','consultoria',
                'estudio de mercado','due diligence','plan maestro','gestion de activos','catastro',
                'informe','diagnostico','estudio de titulos','regularizacion')
    if any(k in t for k in servicio):
        return ('Mandato de SERVICIO',
                'Contratan un servicio profesional inmobiliario: postulacion directa como oferente. '
                'Verificar requisitos de experiencia y garantia de seriedad.')
    if any(k in t for k in busca):
        return ('Estado BUSCA inmueble',
                'El organismo demanda un inmueble en arriendo o compra: oportunidad de colocar una '
                'propiedad de cartera o de representar al propietario. Confirmar si las bases admiten '
                'a un corredor como oferente o exigen al titular del dominio.')
    return ('Por clasificar', 'Revisar bases para determinar el rol comercial.')
