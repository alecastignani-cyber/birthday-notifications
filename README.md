# Birthday Bot — Notificaciones de Cumpleaños del Equipo

Bot automático que envía recordatorios a Slack cuando se acerca el cumpleaños de alguien en el equipo. Corre diariamente via GitHub Actions, sin necesidad de servidores ni infraestructura.

---

## Cómo funciona

1. Los datos del equipo se leen directamente desde un **Google Sheet** (sin archivos CSV locales)
2. GitHub Actions ejecuta `notify.py` todos los días a las 09:00 ART
3. El script calcula cuántos días faltan para cada cumpleaños y envía mensajes a Slack en estos momentos:

| Cuándo | Mensaje |
|--------|---------|
| Todos los lunes | Resumen semanal: quién tiene el próximo cumpleaños y en cuántos días |
| 7 días antes | Recordatorio para planificar el festejo |
| 1 día antes | Recordatorio de que mañana es el cumple |
| El día del cumple | Mensaje de felicitaciones al canal |

### Ejemplo de mensajes en Slack

```
📅 *Resumen semanal* — El próximo cumpleaños del equipo es el de *Gustavo Esteban Tubino* (20/04), en 42 días

🎂 *Recordatorio de cumpleaños* — En 7 días es el cumple de *Gabriela Lezcano* (29/02). ¡Buen momento para planificar el festejo!

🎂 *¡Mañana es el cumpleaños de Luis Regalado!* (21/08) No te olvides de felicitarlo/a 😊

🎉 *¡HOY es el cumpleaños de Alejandro Castignani!* (02/10) ¡Muchas felicidades, Alejandro! 🥳🎊
```

---

## Estructura del proyecto

```
.
├── notify.py                  # Script principal
├── requirements.txt           # Dependencias: gspread + google-auth
├── .github/
│   └── workflows/
│       └── birthday-check.yml # Cron job de GitHub Actions (09:00 ART diario)
└── CLAUDE.md                  # Instrucciones para Claude Code (AI assistant)
```

---

## Fuente de datos: Google Sheets

El equipo se gestiona en este Google Sheet (acceso restringido, solo para el equipo):

> [Cumpleaños del Equipo Casti](https://docs.google.com/spreadsheets/d/1mPmtxdZsZLu0XpR8ZzSDTCrxxnwbChDgIxwuknW-wpc)

El bot lee la primera hoja. La estructura esperada es:

| Fila | Descripción |
|------|-------------|
| 1 | Auxiliar (ignorada) |
| 2 | Headers |
| 3+ | Datos del equipo |

| Columna | Header | Formato | Ejemplo |
|---------|--------|---------|---------|
| C | `Nombre` | Texto libre | `Gabriela Lezcano` |
| D | `Fecha de cumpleaños` | DD/MM o DD/MM/AAAA | `29/02` o `29/02/1980` |

Para agregar o editar personas del equipo, simplemente editá el Google Sheet directamente — el bot tomará los cambios en la próxima ejecución.

> Caso especial: si alguien nació el 29/02 (año bisiesto), el bot notifica el 28/02 en años no bisiestos.

---

## Cómo adaptarlo para tu equipo

### 1. Forkeá o copiá el repositorio

En GitHub, usá **Fork** para crear tu propia copia del repo bajo tu cuenta o la de tu equipo.

### 2. Creá tu propio Google Sheet

Creá un Google Sheet con dos columnas: `nombre` y `cumpleanos` (formato DD/MM). Copiá el ID del Sheet desde la URL:

```
https://docs.google.com/spreadsheets/d/  ← ID →  /edit
```

Actualizá la constante `SHEET_ID` en [notify.py](notify.py).

### 3. Generá tus credenciales de Google

El bot usa OAuth2 con tu cuenta de Google. Necesitás generar un JSON de credenciales con `gcloud`:

```bash
gcloud auth login --enable-gdrive-access
```

Luego extraé las credenciales generadas:

```bash
python3 -c "
import sqlite3, json
db = sqlite3.connect('/Users/TU_USUARIO/.config/gcloud/credentials.db')
row = db.execute('SELECT value FROM credentials LIMIT 1').fetchone()
creds = json.loads(row[0])
print(json.dumps({
  'type': 'authorized_user',
  'client_id': creds['client_id'],
  'client_secret': creds['client_secret'],
  'refresh_token': creds['refresh_token']
}))
"
```

### 4. Agregá los secrets en GitHub

En tu repositorio: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Valor |
|--------|-------|
| `SLACK_WEBHOOK_URL` | URL del webhook de Slack (ver paso siguiente) |
| `GOOGLE_CREDENTIALS_JSON` | El JSON generado en el paso anterior |

### 5. Creá el webhook de Slack

1. En Slack, andá a **Apps** → **Workflow Builder** → **New Workflow**
2. Elegí **Webhook** como trigger
3. Configurá que el workflow postee en el canal de tu equipo usando la variable `text`
4. Copiá la URL del webhook (formato: `https://hooks.slack.com/triggers/...`)

### 6. Probalo manualmente

En **Actions → Birthday Notifications → Run workflow** podés disparar el script en cualquier momento para verificar que funciona.

---

## Ejecutar localmente

```bash
pip install -r requirements.txt

SLACK_WEBHOOK_URL=https://hooks.slack.com/triggers/... \
GOOGLE_CREDENTIALS_JSON='{"type":"authorized_user","client_id":"...","client_secret":"...","refresh_token":"..."}' \
python notify.py
```

Output esperado:

```
[2025-10-02] Verificando cumpleaños para 14 personas...
  ✓ Enviado (HTTP 200): 🎉 *¡HOY es el cumpleaños de Alejandro Castignani!*...
[2025-10-02] 1 notificación(es) enviadas.
```

---

## Mejorarlo con Claude Code (VS Code)

Este proyecto incluye un archivo `CLAUDE.md` con contexto del dominio. Esto permite que Claude Code entienda el proyecto desde el primer mensaje.

### Instalación de Claude Code en VS Code

1. Abrí VS Code
2. Andá a **Extensions** (`Cmd+Shift+X` en Mac / `Ctrl+Shift+X` en Windows)
3. Buscá **Claude Code** (publicado por Anthropic)
4. Instalá la extensión
5. Abrí la carpeta del proyecto: **File → Open Folder**
6. Abrí el panel de Claude Code con `` Ctrl+` `` o desde la barra lateral

### Primeros prompts sugeridos para extender el bot

```
Modificar los mensajes de Slack para que incluyan un emoji personalizado por persona
```

```
Agregar soporte para notificar también por email usando la librería estándar smtplib
```

```
Crear un script de prueba que simule la fecha de hoy para verificar todos los mensajes
```

```
Cambiar el horario de ejecución del cron a las 08:00 ART en vez de las 09:00
```

Claude Code leerá el código existente antes de proponer cambios, por lo que las sugerencias serán coherentes con la arquitectura actual.

---

## Secrets requeridos en GitHub

| Secret | Descripción |
|--------|-------------|
| `SLACK_WEBHOOK_URL` | URL del Workflow Builder trigger de Slack |
| `GOOGLE_CREDENTIALS_JSON` | JSON con credenciales OAuth2 de Google (`client_id`, `client_secret`, `refresh_token`) |

---

## Casos límite manejados

- **Año bisiesto (29/02)**: en años no bisiestos, la notificación se envía el 28/02
- **Fechas faltantes o inválidas**: se omiten con una advertencia en el log, sin interrumpir el resto
- **Sin cumpleaños ese día**: el script termina con un log informativo, sin enviar nada a Slack
