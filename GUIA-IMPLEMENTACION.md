# Puesta en marcha del radar de licitaciones

Guía completa: de la carpeta que tienes ahora a un sistema que corre solo los lunes a las
11:00 y los miércoles a las 21:00, publica en **chilecompra.gamma-re.com**, te avisa por
WhatsApp y te manda el Excel a **luisfelipe@realsachile.com**.

Tiempo total: **35-45 minutos**, más la espera de propagación DNS.

---

## Antes de empezar

Ten a mano:

| Qué | Dónde | Ya lo tienes |
|---|---|---|
| Cuenta de GitHub | github.com | Sí — necesito tu usuario para el paso 3 |
| Acceso al DNS de gamma-re.com | GoDaddy (confirmado: `ns63/ns64.domaincontrol.com`) | Sí |
| API key de CallMeBot | WhatsApp | Sí |
| Cuenta de Resend | resend.com — se crea en el paso 5 | No |

**Una decisión previa que condiciona todo lo demás:** GitHub Pages con dominio propio
**solo funciona en repositorios públicos** si tu cuenta es gratuita. Con repo privado
necesitas GitHub Pro (USD 4/mes). El contenido no es confidencial — son licitaciones
públicas — pero el dashboard sí revela qué oportunidades estás siguiendo y con qué
criterio. Si eso te incomoda, toma Pro antes de seguir.

---

## Paso 1 — Descomprimir y revisar

Descomprime `radar-mp-cloud.zip`. Deberías ver:

```
radar-mp-cloud/
├── .github/workflows/radar.yml    ← el cron y toda la orquestación
├── pipeline/                      ← el motor (7 scripts de Python)
├── data/cache_detalles.json       ← caché precargado: te ahorra la primera corrida larga
├── docs/CNAME                     ← contiene chilecompra.gamma-re.com
├── requirements.txt
└── README.md
```

**No borres `docs/CNAME`.** Es el archivo que le dice a GitHub Pages que sirva el sitio en
tu dominio; si desaparece, el dominio propio se cae y el sitio vuelve a la URL genérica.

---

## Paso 2 — Crear el repositorio en GitHub

En github.com: **New repository**.

- Nombre sugerido: `radar-licitaciones`
- Visibilidad: **Public** (salvo que tengas Pro — ver la decisión previa)
- **No** marques "Add a README file" — ya viene uno

En la pantalla siguiente GitHub te muestra la URL del repo. Cópiala.

---

## Paso 3 — Subir el contenido

En la Terminal del Mac, dentro de la carpeta descomprimida:

```bash
cd ruta/a/radar-mp-cloud
git init
git add .
git commit -m "Radar de licitaciones"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/radar-licitaciones.git
git push -u origin main
```

Reemplaza `TU-USUARIO` por tu usuario real de GitHub. Si te pide contraseña, GitHub ya no
acepta la de tu cuenta: usa un **Personal Access Token** (`Settings → Developer settings →
Personal access tokens → Tokens (classic) → Generate new token`, con permiso `repo`) y
pégalo donde pide la contraseña.

> Si prefieres no usar Terminal: en el repo vacío, **uploading an existing file** y arrastra
> todo. Ojo: el navegador **no sube carpetas ocultas**, y `.github/workflows/radar.yml` es
> justamente una — sin ella no hay automatización. Por eso conviene la Terminal.

---

## Paso 4 — Activar GitHub Pages con el dominio propio

### 4.1 Publicar el sitio

`Settings → Pages`

- **Source:** Deploy from a branch
- **Branch:** `main` · carpeta **`/docs`** → **Save**

Espera 1-2 minutos. Aparece la URL genérica `https://TU-USUARIO.github.io/radar-licitaciones/`.
Ábrela: deberías ver el dashboard con las 10 licitaciones de la corrida de prueba que ya
viene cargada.

### 4.2 Declarar el dominio

En la misma pantalla, **Custom domain**: escribe `chilecompra.gamma-re.com` → **Save**.

GitHub va a mostrar un error de verificación DNS. **Es lo esperado** — el registro DNS
todavía no existe. Se resuelve en el paso siguiente.

---

## Paso 5 — Crear el registro DNS en GoDaddy

Entra a GoDaddy → tu dominio `gamma-re.com` → **DNS** → **Administrar zonas** →
**Agregar registro**.

| Campo | Valor |
|---|---|
| Tipo | **CNAME** |
| Nombre / Host | `chilecompra` |
| Valor / Apunta a | `TU-USUARIO.github.io` |
| TTL | 600 segundos (1 hora también sirve) |

**Tres errores que cuestan una tarde entera:**

1. En el campo **Nombre** va solo `chilecompra`, **no** `chilecompra.gamma-re.com`. GoDaddy
   completa el dominio solo; si escribes el nombre completo terminas con
   `chilecompra.gamma-re.com.gamma-re.com`.
2. En **Valor** va `TU-USUARIO.github.io`, **sin** `https://` y **sin** el nombre del repo.
3. Verifica que no exista ya otro registro A o CNAME con el host `chilecompra`. Dos
   registros para el mismo host se pelean y el resultado es errático. (Lo revisé: hoy el
   subdominio está libre.)

### 5.1 Confirmar que propagó

En la Terminal:

```bash
dig +short CNAME chilecompra.gamma-re.com
```

Debe responder `tu-usuario.github.io.`. Suele tardar 10-30 minutos; si GoDaddy te dejó un
TTL largo, hasta 1 hora.

### 5.2 Cerrar el círculo en GitHub

Vuelve a `Settings → Pages`. El error de verificación desaparece. Cuando se habilite,
marca **Enforce HTTPS** (GitHub emite el certificado solo; puede tardar otros 15 minutos).

Prueba `https://chilecompra.gamma-re.com` — ahí queda el dashboard, y **esa URL no cambia
nunca**: cada corrida sobrescribe el contenido.

---

## Paso 6 — Configurar el envío del Excel (Resend)

### 6.1 Crear la cuenta

En resend.com, **Sign up** (plan gratuito: 3.000 correos al mes, 100 por día — de sobra
para 8 corridas mensuales).

### 6.2 Verificar un subdominio de envío

`Domains → Add Domain` → escribe **`envios.gamma-re.com`**.

> **Usa el subdominio, no `gamma-re.com` a secas.** Tu dominio raíz ya tiene un SPF
> apuntando a Microsoft 365 (`v=spf1 include:spf.protection.outlook.com -all`), y ese `-all`
> significa "rechaza todo lo que no venga de Microsoft". Si intentas verificar el dominio
> raíz en Resend tienes que editar ese SPF, y un error ahí te tumba el correo corporativo de
> Gamma. Con un subdominio de envío, Resend crea su propio SPF aislado y el correo de la
> empresa ni se entera.

Resend te muestra 3 registros (MX y dos TXT). Agrégalos en GoDaddy tal como aparecen, con
una traducción importante: **GoDaddy pide el nombre relativo al dominio**, así que a cada
host de Resend le quitas `.gamma-re.com` del final.

| Lo que muestra Resend | Lo que escribes en GoDaddy (campo Nombre) |
|---|---|
| `send.envios.gamma-re.com` | `send.envios` |
| `resend._domainkey.envios.gamma-re.com` | `resend._domainkey.envios` |

Los valores (el servidor MX, el SPF y la llave DKIM larga) se copian **literales** desde
Resend, sin tocar. Vuelve a Resend y pulsa **Verify DNS Records**. Verde en los tres = listo.

### 6.3 Generar la API key

`API Keys → Create API Key`, permiso **Sending access**. Cópiala ahora — no se vuelve a
mostrar.

---

## Paso 7 — Cargar secretos y variables en GitHub

`Settings → Secrets and variables → Actions`

Pestaña **Secrets** → *New repository secret*:

| Nombre | Valor |
|---|---|
| `CALLMEBOT_APIKEY` | tu key de CallMeBot |
| `WHATSAPP_PHONE` | `+56933876335` |
| `RESEND_API_KEY` | la key del paso 6.3 |
| `MP_TICKET` | *(opcional)* tu ticket propio de Mercado Público |

Pestaña **Variables** → *New repository variable*:

| Nombre | Valor |
|---|---|
| `PAGES_URL` | `https://chilecompra.gamma-re.com` |
| `EMAIL_DESTINO` | `luisfelipe@realsachile.com` |
| `EMAIL_REMITENTE` | `Radar de Licitaciones <radar@envios.gamma-re.com>` |

> La distinción importa: los **secrets** quedan cifrados y no se pueden leer después ni
> aparecen en los logs; las **variables** son texto plano visible. Una API key jamás va como
> variable.

---

## Paso 8 — Probar

`Actions → Radar de licitaciones → Run workflow` → deja **forzar** en `true` (eso salta el
guardia de ventana horaria) → **Run workflow**.

Toma entre 5 y 10 minutos con el ticket público. Al terminar deberías tener:

- [ ] Los 11 pasos en verde en la pestaña Actions
- [ ] `https://chilecompra.gamma-re.com` actualizado, con las nuevas destacadas en verde
- [ ] Un WhatsApp con el link
- [ ] El correo con el Excel adjunto en luisfelipe@realsachile.com
- [ ] Un commit nuevo en el repo con el histórico actualizado

A partir de ahí corre solo: **lunes 11:00** y **miércoles 21:00**, hora de Santiago.

---

## Si algo falla

| Síntoma | Causa y solución |
|---|---|
| Pages dice "Domain does not resolve" | El CNAME aún no propaga. Verifica con `dig +short CNAME chilecompra.gamma-re.com` y espera. |
| El sitio carga sin estilos o da 404 | La carpeta de publicación quedó en `/` en vez de `/docs`. Corrígela en Settings → Pages. |
| Vuelve la URL genérica y se pierde el dominio | Se borró `docs/CNAME`. El script `publicar.py` lo recrea, pero revisa que esté en el repo. |
| Resend responde 403 / "domain not verified" | Los tres registros DNS no están verdes, o el remitente no coincide con el dominio verificado. El `EMAIL_REMITENTE` debe terminar en `@envios.gamma-re.com`. |
| No llega el WhatsApp | CallMeBot devuelve el motivo en el log del paso "Avisar por WhatsApp". Lo más común: la API key expira si no la usas en mucho tiempo — se reactiva escribiéndole de nuevo al bot. |
| El barrido se queda en 429 | Rate limit del ticket público. El workflow reintenta hasta 5 veces; si igual falla, pide tu propio ticket a la mesa de ayuda de Mercado Público y cárgalo en `MP_TICKET`. |
| El workflow corre y dice "OMITIR" | Es correcto: el guardia horario descartó el disparo que no correspondía a la hora de Chile. Para forzarlo, usa Run workflow con *forzar* en `true`. |
| Todo sale marcado como NUEVA cada vez | El commit del histórico no se está guardando. Revisa que el paso "Guardar historico y dashboard" esté en verde y que el repo tenga permisos de escritura (`Settings → Actions → General → Workflow permissions → Read and write`). |

---

## Cómo funciona la marca de "nueva"

Es lo primero que vas a mirar cada lunes, así que conviene entender qué significa:

- Una licitación es **NUEVA** cuando su código no aparecía en **ninguna corrida anterior**.
  La comparación es contra el histórico acumulado en `data/historico.json`, no contra la
  fecha de publicación del aviso. Es la definición correcta para tu uso: lo relevante es
  "esto no lo había visto", no "esto se publicó hoy".
- En el **Excel**: columna `Nueva` (SI/NO) como primera columna, y toda la fila con fondo
  verde. El fondo ámbar marca las que ya estaban pero cambiaron de estado, fecha de cierre
  o monto — el detalle exacto del cambio va en la columna `Novedad`.
- En el **dashboard**: banda verde gruesa al costado, etiqueta NUEVA en la esquina, y un
  filtro **"Solo nuevas"** al inicio de la barra.
- El histórico se guarda en el repo en cada corrida. **Eso es lo que da continuidad**: si
  se pierde, la corrida siguiente marca todo como nuevo.

---

## Costos

| Componente | Costo |
|---|---|
| GitHub Actions (repo público) | Gratis, sin límite de minutos |
| GitHub Pages | Gratis |
| Resend | Gratis hasta 3.000 correos/mes (usarás ~8) |
| CallMeBot | Gratis, uso personal |
| API de Mercado Público | Gratis |
| **Total** | **USD 0** — salvo GitHub Pro (USD 4/mes) si quieres el repo privado |
