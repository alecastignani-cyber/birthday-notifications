# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

**NOTIFICACIONES_CUMPLEAÑOS_EQUIPO_CASTI** — Bot que notifica vía Slack cuando se acerca el cumpleaños de alguien del equipo (LH + Scheduling + Topology — Campana).

## Cómo funciona

1. `equipo.csv` contiene el listado de personas y fechas de cumpleaños
2. `notify.py` se ejecuta diariamente vía GitHub Actions
3. Si alguien cumple años en 5 días, mañana o hoy → envía mensaje al canal de Slack configurado

## Commands

- Instalar dependencias: `pip install -r requirements.txt`
- Probar localmente: `SLACK_BOT_TOKEN=xoxb-... SLACK_CHANNEL_ID=C... python notify.py`

## Architecture

- **`equipo.csv`** — Fuente de datos. Columnas: `nombre`, `cumpleanos` (formato DD/MM). Editar directamente para agregar/quitar personas.
- **`notify.py`** — Script Python. Lee el CSV, calcula días al próximo cumpleaños, envía mensajes a Slack via `slack_sdk`.
- **`.github/workflows/birthday-check.yml`** — Cron job en GitHub Actions. Corre todos los días a las 09:00 ART (12:00 UTC).

## Secrets requeridos en GitHub

| Secret | Descripción |
|---|---|
| `SLACK_WEBHOOK_URL` | URL del Workflow Builder trigger de Slack (`https://hooks.slack.com/triggers/...`) |

## Casos especiales manejados

- **Gabriela Lezcano (29/02)**: en años no bisiestos notifica el 28/02
- **Fechas faltantes**: si una persona no tiene fecha en el CSV, se omite con advertencia en el log
