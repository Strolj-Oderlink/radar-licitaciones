# Radar de licitaciones — contexto del proyecto

<!-- Lo carga Claude Code vía el import de CLAUDE.md. -->

Detector de licitaciones de **Mercado Público** que calzan con los servicios de
**Gamma Real Estate / Realsa Brokers**: corretaje, arriendo, venta, tasación,
valorización y consultoría inmobiliaria. Dueño: **Felipe (LF)**, Santiago de
Chile.

Barre la API oficial, puntúa cada aviso con una taxonomía propia, y entrega
dashboard, Excel con histórico, correo y aviso por WhatsApp. Corre en GitHub
Actions + GitHub Pages, sin servidor propio.

Estado al 01/10/2026: **funcionando**. Corre cada cuatro días; la última entrega
fue el 30/09 con 3 licitaciones vigentes.

---

## Lo primero, siempre

El repositorio **no tiene suite de pruebas**. Es su principal deuda técnica: el
proyecto hermano (`agenda-cloud`) tiene 221 aserciones que han atajado varios
bugs antes de producción. Si vas a tocar `taxonomia.py` o `scan.py`, considera
escribir pruebas primero — la taxonomía es pura lógica sin red y es trivial de
probar.

Para probar a mano, desde `Actions → Radar de licitaciones → Run workflow`, con
*forzar* en `true` para saltarse la ventana horaria. Tarda 5-10 minutos con el
ticket público, menos de 1 minuto con ticket propio.

```bash
pip install -r requirements.txt
MP_DATA=./data MP_OUT=./salidas python3 pipeline/scan.py     # barrido
MP_DATA=./data MP_OUT=./salidas python3 pipeline/run.py      # entregables
```

---

## Mapa

| Archivo | Qué hace |
|---|---|
| `.github/workflows/radar.yml` | Cron, orquestación, commit del histórico, envíos |
| `pipeline/ventana.py` | Guardia horario y candado del día |
| `pipeline/scan.py` | Barrido de la API, prefiltro, detalle, scoring, filtros |
| `pipeline/taxonomia.py` | **El criterio**: términos, pesos, exclusiones, clasificación |
| `pipeline/reportes.py` | Excel con histórico y resumen ejecutivo |
| `pipeline/dashboard.py` | Dashboard HTML autocontenido |
| `pipeline/publicar.py` | Arma `docs/` para Pages y el texto del aviso |
| `pipeline/notificar.py` | Aviso por WhatsApp (CallMeBot) |
| `pipeline/enviar_correo.py` | Excel de respaldo por Resend |
| `pipeline/run.py` | Emite los tres entregables desde la última corrida |

`DOCUMENTACION.md` tiene 530 líneas con el detalle del motor de matching, los
umbrales de monto, la detección de novedad y la conversión a UF. **Léelo antes
de tocar la taxonomía**: cada señal, exclusión y corte está justificado ahí.

---

## Invariantes — no deshacer sin leer por qué

1. **`data/` se commitea en cada corrida.** Es la caché de detalles y el
   histórico; es lo que da continuidad y lo que permite detectar qué es nuevo.
   Sin eso, cada corrida reportaría todo como novedad.
2. **`docs/CNAME` fija el dominio propio en Pages. No borrar.**
3. **El guardia horario existe por el cambio de huso.** GitHub programa en UTC y
   Chile alterna UTC-4 / UTC-3, así que el workflow dispara en los dos horarios
   posibles y `ventana.py` deja pasar solo el correcto. El candado del día evita
   la corrida doble.
4. **Hay un disparo diario extra** (`41 16 * * *`) solo para mantener el
   repositorio activo: GitHub deshabilita los schedules tras 60 días de
   inactividad. No es una corrida de verdad; el guardia lo descarta.
5. **Sin `MP_TICKET` propio se usa el ticket público**, con ~25% de respuestas
   429 y reintentos. Funciona, pero tarda 5-10 minutos en vez de 1.
6. **El WhatsApp lleva solo el link**, por decisión explícita de Felipe:
   CallMeBot transmite el texto en claro por su propio servidor.

---

## Cómo trabaja Felipe

- **Español de Chile**, tono ejecutivo. Sin relleno.
- **Un solo bloque de terminal por vez**, copiable de una.
- Él pega los comandos y hace `git push`; Claude edita los archivos.
- **Verificar antes de afirmar.** Versiones, endpoints, menús de consolas:
  comprobar, no recordar.

### La trampa que ya costó caro

**Para saber si el sistema corre, mirar lo que entregó —el correo, el
dashboard— no el repositorio local.** La carpeta del Mac puede llevar semanas
sin `git pull` mientras el bot commitea a GitHub en cada corrida. Leer el
historial local como si fuera el estado real llevó a declarar muerto un sistema
que funcionaba perfecto. Hacer `git pull` **antes** de diagnosticar nada.

---

## Pendientes conocidos

- **Sin suite de pruebas.** Lo más valioso que se le puede agregar.
- **Sin aviso de fallo.** Si una corrida falla, no avisa: la única señal es que
  el correo no llegue. El proyecto hermano resolvió esto con un paso
  `if: failure() || cancelled()` que manda WhatsApp y correo con el traceback
  — vale la pena portarlo (ver `agenda-cloud/pipeline/alerta.py`).
- **Pasos sin `always()`.** En GitHub Actions, si un paso falla, los siguientes
  **se saltan**. Publicar en Pages y enviar el correo son cosas independientes,
  pero hoy están encadenadas: un fallo al publicar deja a Felipe sin el Excel.
  Mismo bug que tuvo la agenda.

---

## Proyecto hermano

`agenda-cloud` (repo `agenda-gamma`) comparte infraestructura y convenciones:
GitHub Actions, Cloudflare/Pages, Resend, CallMeBot, el guardia horario con
doble cron y el candado del día. Su `AGENDA-INCIDENTES.md` documenta catorce
incidentes con la defensa que quedó de cada uno; varios aplican aquí tal cual.
