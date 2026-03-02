import csv
import os
import calendar
import json
import urllib.request
import urllib.error
from datetime import date


def cargar_equipo(path="equipo.csv"):
    equipo = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nombre = row["nombre"].strip()
            cumple = row["cumpleanos"].strip()
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


def main():
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("ERROR: Falta la variable de entorno SLACK_WEBHOOK_URL")
        return

    equipo = cargar_equipo()
    hoy = date.today()
    notificaciones = 0

    print(f"[{hoy}] Verificando cumpleaños para {len(equipo)} personas...")

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

        if dias == 5:
            msg = (
                f"🎂 *Recordatorio de cumpleaños* — En 5 días es el cumple de "
                f"*{nombre_completo}* ({fecha_fmt}). ¡Buen momento para planificar el festejo!"
            )
            enviar_slack(webhook_url, msg)
            notificaciones += 1

        elif dias == 1:
            msg = (
                f"🎂 *¡Mañana es el cumpleaños de {nombre_completo}!* "
                f"No te olvides de felicitarlo/a 😊"
            )
            enviar_slack(webhook_url, msg)
            notificaciones += 1

        elif dias == 0:
            msg = (
                f"🎉 *¡HOY es el cumpleaños de {nombre_completo}!* "
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
