from core import estados

def interpretar(texto):

    if "salir" in texto:
        return "SALIR"

    if "cultubot" in texto:

        estados.ACTIVADO = True
        return "ACTIVAR"

    if not estados.ACTIVADO:
        return "DORMIDO"

    if "malecon" in texto:
        return "DIBUJAR_MALECON"

    if "cristo rey" in texto:
        return "DIBUJAR_CRISTOREY"

    return "NO_ENTIENDO"