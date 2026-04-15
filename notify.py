import os
import calendar
import json
import urllib.request
import urllib.error
from datetime import date

import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest

SHEET_ID = "1mPmtxdZsZLu0XpR8ZzSDTCrxxnwbChDgIxwuknW-wpc"


def cargar_equipo():
    creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds = Credentials(
        token=None,
        refresh_token=creds_info["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=creds_info["client_id"],
        client_secret=creds_info["client_secret"],
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    creds.refresh(GoogleRequest())
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(SHEET_ID).get_worksheet(0)
    # Fila 1: auxiliar, Fila 2: headers → datos desde fila 3 (índice 2)
    # Columna C (índice 2): Nombre, Columna D (índice 3): Fecha de cumpleaños
    rows = worksheet.get_all_values()
    equipo = []
    for row in rows[2:]:
        nombre = row[2].strip() if len(row) > 2 else ""
        cumple = row[3].strip() if len(row) > 3 else ""
        if nombre and cumple:
            equipo.append({"nombre": nombre, "cumpleanos": cumple})
    return equipo


def parsear_fecha(fecha_str):
    """Parsea DD/MM, DD/MM/YY o DD/MM/YYYY. Devuelve (day, month) o None."""
    parts = fecha_str.strip().split("/")
    if len(parts) >= 2:
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            pass
    return None


def dias_hasta_cumple(day, month, hoy=None):
    """Calcula los días que faltan para el próximo cumpleaños. 0 = hoy."""
    if hoy is None:
        hoy = date.today()

    year = hoy.year

    # Feb 29 en años no bisiestos → usar Feb 28
    if month == 2 and day == 29 and not calendar.isleap(year):
        day = 28

    try:
        cumple = date(year, month, day)
    except ValueError:
        return None

    if cumple < hoy:
        year += 1
        if month == 2 and day == 29 and not calendar.isleap(year):
            day = 28
        try:
            cumple = date(year, month, day)
        except ValueError:
            return None

    return (cumple - hoy).days


def enviar_slack(webhook_url, mensaje):
    payload = json.dumps({"text": mensaje}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"  ✓ Enviado (HTTP {resp.status}): {mensaje[:80]}...")
    except urllib.error.HTTPError as e:
        print(f"  ✗ Error HTTP {e.code}: {e.read().decode()}")
    except urllib.error.URLError as e:
        print(f"  ✗ Error de conexión: {e.reason}")


def resumen_semanal(webhook_url, equipo, hoy):
    """Envía el próximo cumpleaños del equipo. Se llama solo los lunes."""
    candidatos = []
    for persona in equipo:
        fecha = parsear_fecha(persona["cumpleanos"])
        if not fecha:
            continue
        day, month = fecha
        dias = dias_hasta_cumple(day, month, hoy)
        if dias is not None:
            candidatos.append((dias, day, month, persona["nombre"]))

    if not candidatos:
        return

    candidatos.sort()
    dias, day, month, nombre_completo = candidatos[0]
    fecha_fmt = f"{day:02d}/{month:02d}"

    if dias == 0:
        cuando = "¡hoy mismo! 🎉"
    elif dias == 1:
        cuando = "¡mañana!"
    else:
        cuando = f"en {dias} días"

    msg = (
        f"📅 *Resumen semanal* — El próximo cumpleaños del equipo es el de "
        f"*{nombre_completo}* ({fecha_fmt}), {cuando}"
    )
    enviar_slack(webhook_url, msg)


def main():
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("ERROR: Falta la variable de entorno SLACK_WEBHOOK_URL")
        return

    equipo = cargar_equipo()
    hoy = date.today()
    notificaciones = 0

    print(f"[{hoy}] Verificando cumpleaños para {len(equipo)} personas...")

    if hoy.weekday() == 0:  # 0 = lunes
        print("  → Lunes: enviando resumen semanal...")
        resumen_semanal(webhook_url, equipo, hoy)
        notificaciones += 1

    for persona in equipo:
        fecha = parsear_fecha(persona["cumpleanos"])
        if not fecha:
            print(f"  ⚠ Fecha inválida para {persona['nombre']}: {persona['cumpleanos']}")
            continue

        day, month = fecha
        dias = dias_hasta_cumple(day, month, hoy)

        if dias is None:
            continue

        nombre = persona["nombre"].split()[0]  # primer nombre para el saludo
        nombre_completo = persona["nombre"]
        fecha_fmt = f"{day:02d}/{month:02d}"

        if dias == 7:
            msg = (
                f"🎂 *Recordatorio de cumpleaños* — En 7 días es el cumple de "
                f"*{nombre_completo}* ({fecha_fmt}). ¡Buen momento para planificar el festejo!"
            )
            enviar_slack(webhook_url, msg)
            notificaciones += 1

        elif dias == 1:
            msg = (
                f"🎂 *¡Mañana es el cumpleaños de {nombre_completo}!* ({fecha_fmt}) "
                f"No te olvides de felicitarlo/a 😊"
            )
            enviar_slack(webhook_url, msg)
            notificaciones += 1

        elif dias == 0:
            msg = (
                f"🎉 *¡HOY es el cumpleaños de {nombre_completo}!* ({fecha_fmt}) "
                f"¡Muchas felicidades, {nombre}! 🥳🎊"
            )
            enviar_slack(webhook_url, msg)
            notificaciones += 1

    if notificaciones == 0:
        print(f"[{hoy}] Sin cumpleaños para notificar hoy.")
    else:
        print(f"[{hoy}] {notificaciones} notificación(es) enviadas.")


if __name__ == "__main__":
    main()
