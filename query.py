import os

from notify import cargar_equipo, parsear_fecha, dias_hasta_cumple, enviar_slack


def buscar_persona(equipo, nombre_query):
    nombre_query = nombre_query.strip().lower()
    return [p for p in equipo if nombre_query in p["nombre"].lower()]


def main():
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    nombre_query = os.environ.get("QUERY_NOMBRE", "").strip()

    if not webhook_url:
        print("ERROR: Falta SLACK_WEBHOOK_URL")
        return

    if not nombre_query:
        enviar_slack(webhook_url, "⚠️ No se especificó ningún nombre para consultar.")
        return

    from datetime import date
    equipo = cargar_equipo()
    hoy = date.today()
    matches = buscar_persona(equipo, nombre_query)

    if not matches:
        enviar_slack(webhook_url, f"❓ No encontré a nadie con *{nombre_query}* en el equipo.")
        return

    if len(matches) == 1:
        persona = matches[0]
        fecha = parsear_fecha(persona["cumpleanos"])
        if not fecha:
            enviar_slack(webhook_url, f"⚠️ *{persona['nombre']}* está en el equipo pero no tiene fecha de cumpleaños registrada.")
            return

        day, month = fecha
        dias = dias_hasta_cumple(day, month, hoy)
        fecha_fmt = f"{day:02d}/{month:02d}"

        if dias == 0:
            msg = f"🎉 *{persona['nombre']}* cumple años *hoy* ({fecha_fmt}). ¡A felicitarlo/a!"
        elif dias == 1:
            msg = f"🎂 *{persona['nombre']}* cumple años *mañana* ({fecha_fmt})."
        else:
            msg = f"📅 *{persona['nombre']}* cumple el *{fecha_fmt}* — faltan *{dias} días*."

        enviar_slack(webhook_url, msg)

    else:
        lines = [f"🔍 Encontré {len(matches)} personas con *{nombre_query}*:"]
        for persona in matches:
            fecha = parsear_fecha(persona["cumpleanos"])
            if fecha:
                day, month = fecha
                dias = dias_hasta_cumple(day, month, hoy)
                fecha_fmt = f"{day:02d}/{month:02d}"
                lines.append(f"• *{persona['nombre']}* — {fecha_fmt} (faltan {dias} días)")
            else:
                lines.append(f"• *{persona['nombre']}* — sin fecha registrada")
        enviar_slack(webhook_url, "\n".join(lines))


if __name__ == "__main__":
    main()
