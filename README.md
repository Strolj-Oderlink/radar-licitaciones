# Radar de licitaciones — Mercado Público (Gamma / Realsa Brokers)

Barre las ~4.500 licitaciones activas de Mercado Público, aísla las que calzan con los
servicios inmobiliarios de Gamma y Realsa Brokers, publica un dashboard en GitHub Pages
y avisa por WhatsApp con el link.

**Corre en la nube (GitHub Actions), sin depender de tu computador.**

- **Lunes 11:00** y **miércoles 21:00**, hora de Santiago.
- Dashboard siempre en la misma URL: **https://chilecompra.gamma-re.com** (se sobrescribe).
- Aviso por WhatsApp con el link + Excel de respaldo por correo a luisfelipe@realsachile.com.
- Las licitaciones nuevas quedan marcadas en el HTML y en la columna `Nueva` del Excel.

---

## 👉 Puesta en marcha

**La guía completa paso a paso está en [`GUIA-IMPLEMENTACION.md`](GUIA-IMPLEMENTACION.md)** —
repo, Pages, DNS en GoDaddy, Resend, secretos y prueba. Lo de abajo es el resumen.

---

## Resumen de la configuración

### 1. Crear el repositorio

Sube este contenido a un repo nuevo en tu cuenta de GitHub. Puede ser **privado**: GitHub
Pages funciona en repos privados con cuenta Pro; si tu cuenta es gratuita y quieres el
link público en el celular, el repo debe ser público. El dashboard no contiene datos
confidenciales — son licitaciones públicas — pero sí revela qué estás mirando.

```bash
cd radar-mp-cloud
git init && git add . && git commit -m "Radar de licitaciones"
git branch -M main
git remote add origin https://github.com/<tu-usuario>/radar-licitaciones-mp.git
git push -u origin main
```

### 2. Activar GitHub Pages

`Settings → Pages → Source: Deploy from a branch → Branch: main, carpeta /docs → Save`

Te queda una URL del tipo `https://<tu-usuario>.github.io/radar-licitaciones-mp/`.

### 3. Obtener la API key de WhatsApp (CallMeBot)

1. Agrega a tus contactos el número del bot: **+34 613 01 49 37**
2. Escríbele por WhatsApp, exactamente: `I allow callmebot to send me messages`
3. En menos de 2 minutos te responde con tu APIKEY. (Si no llega, reintenta a las 24 h.)

> La API gratuita de CallMeBot es solo para uso personal y envía texto, no adjuntos —
> por eso el mensaje lleva el link al dashboard. Si más adelante quieres adjuntar el
> Excel o el PDF, hay que pasar a Twilio o a la Cloud API de Meta.

### 4. Cargar secretos y variables

`Settings → Secrets and variables → Actions`

| Tipo | Nombre | Valor |
|---|---|---|
| Secret | `CALLMEBOT_APIKEY` | la key del paso 3 |
| Secret | `WHATSAPP_PHONE` | `+56933876335` |
| Secret | `MP_TICKET` | *(opcional)* tu ticket propio de Mercado Público |
| Secret | `RESEND_API_KEY` | key de Resend para el envío del Excel |
| Variable | `PAGES_URL` | `https://chilecompra.gamma-re.com` |
| Variable | `EMAIL_DESTINO` | `luisfelipe@realsachile.com` |
| Variable | `EMAIL_REMITENTE` | `Radar de Licitaciones <radar@envios.gamma-re.com>` |

### 5. Probar

`Actions → Radar de licitaciones → Run workflow` (deja *forzar* en `true` para saltarse
la ventana horaria). En 5-10 minutos debería llegarte el WhatsApp con el link.

---

## El ticket de Mercado Público

Sin `MP_TICKET` se usa el ticket público de demostración: funciona, pero está muy limitado
(≈25% de respuestas 429) y obliga a reintentar, así que la corrida tarda 5-10 minutos. Con
ticket propio baja a menos de 1 minuto y desaparecen los reintentos. Se solicita a la mesa
de ayuda de Mercado Público.

## Cómo está armado

| Archivo | Rol |
|---|---|
| `.github/workflows/radar.yml` | Cron, orquestación, commit del histórico y envío |
| `pipeline/ventana.py` | Guardia horario: GitHub programa en UTC y Chile cambia de huso, así que el workflow dispara en los dos horarios posibles y este script deja pasar solo el correcto. También evita la corrida doble del mismo día |
| `pipeline/scan.py` | Barrido de la API, prefiltro, detalle, scoring, filtros |
| `pipeline/taxonomia.py` | Términos, pesos, exclusiones y clasificación de oportunidad |
| `pipeline/reportes.py` | Excel con histórico y resumen ejecutivo |
| `pipeline/dashboard.py` | Dashboard HTML autocontenido |
| `pipeline/publicar.py` | Arma `docs/` para Pages y el texto del aviso |
| `pipeline/notificar.py` | Envío del aviso por CallMeBot |
| `pipeline/enviar_correo.py` | Envío del Excel de respaldo por Resend |
| `docs/CNAME` | Fija el dominio propio en Pages — **no borrar** |
| `data/` | Caché de detalles e histórico — **se commitea en cada corrida**, es lo que da continuidad |

## Ajustar el criterio

Los umbrales van como argumentos en el workflow (`--min-rm 500 --min-nacional 2000
--min-dias 1`). Los términos y pesos están en `pipeline/taxonomia.py`.

Para calibrar, no muevas el umbral a ciegas: abre la hoja **Descartes (auditoría)** del
Excel ordenada por score. Los descartes con score alto son los candidatos a falso
negativo y casi siempre revelan un término faltante, no un umbral mal puesto.

## Advertencias de interpretación

- El monto que publica Mercado Público es el del **contrato** (el honorario), no el del
  activo: una tasación de un edificio grande puede aparecer bajo UF 100. Por eso los
  avisos bajo umbral no se descartan, quedan en su propia hoja.
- Muchos organismos ocultan el monto estimado: esos pasan marcados como "no publicado",
  con el rango legal según el tipo de licitación.
- La entidad sugerida (Gamma o Realsa) es una recomendación basada en si el pliego
  pondera experiencia acreditada. La decisión es tuya.
