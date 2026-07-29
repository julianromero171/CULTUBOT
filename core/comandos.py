from core.lugares import LUGARES
from core import estados

def interpretar(texto):

    if "salir" in texto:
        return ("SALIR", None)

    if "cultubot" in texto:
        estados.ACTIVADO = True
        return ("ACTIVAR", None)

    if not estados.ACTIVADO:
        return ("DORMIDO", None)

    for lugar in LUGARES:

        if lugar in texto:

            return ("DIBUJAR", LUGARES[lugar])

    return ("NO_ENTIENDO", None)