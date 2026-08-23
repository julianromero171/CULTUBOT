"""
Convierte texto ya normalizado en una acción concreta.

Este módulo es puro: NO modifica la máquina de estados directamente.
Solo la consulta (para saber en qué estado está) y devuelve un Resultado.
Quien aplica las transiciones de estado es core/acciones.py (Ejecutor).

Flujo de dos pasos para dibujar:
    1) Usuario dice el nombre del lugar (ej. "malecon")
       -> Accion.PREGUNTAR_OPCION, con el Lugar encontrado.
       -> El Ejecutor pasa la máquina a CONFIRMANDO y pregunta qué quiere.
    2) Usuario responde con una de las opciones (dibujo / dibujo con audio / solo audio)
       -> Accion.CONFIRMAR, con la Opcion elegida.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import NamedTuple, Optional

from core.estados import Estado, MaquinaEstados
from core.lugares import Lugar, buscar_lugar


class Accion(Enum):
    SALIR = auto()
    ACTIVAR = auto()
    PREGUNTAR_OPCION = auto()  # se reconoció un lugar, falta elegir qué hacer
    CONFIRMAR = auto()         # se eligió una opción mientras se preguntaba
    NO_ENTIENDE = auto()
    IGNORAR = auto()           # el robot está dormido y no dijeron la palabra de activación


class Opcion(Enum):
    DIBUJO = auto()
    DIBUJO_CON_AUDIO = auto()
    SOLO_AUDIO = auto()


class Resultado(NamedTuple):
    accion: Accion
    lugar: Optional[Lugar] = None
    opcion: Optional[Opcion] = None


def _detectar_opcion(texto: str) -> Optional[Opcion]:
    """Busca las palabras clave sueltas "dibujo"/"audio" en vez de una
    frase completa ("solo audio", "dibujo con audio", etc.) — el
    reconocimiento de Vosk a veces solo capta un fragmento corto (ej.
    "audio" solo, o "el audio"), y una frase completa nunca puede ser
    substring de algo más corto que ella misma: con la lógica anterior
    (buscar la frase completa) esos fragmentos nunca coincidían con
    nada y el usuario se quedaba sin poder confirmar ninguna opción,
    aunque hubiera dicho algo claro. Confirmado en la Pi real.
    """
    tiene_dibujo = "dibujo" in texto
    tiene_audio = "audio" in texto
    if tiene_dibujo and tiene_audio:
        return Opcion.DIBUJO_CON_AUDIO
    if tiene_audio:
        return Opcion.SOLO_AUDIO
    if tiene_dibujo:
        return Opcion.DIBUJO
    return None


def interpretar(texto: str, maquina: MaquinaEstados) -> Resultado:
    if "salir" in texto:
        return Resultado(Accion.SALIR)

    if "cultubot" in texto:
        return Resultado(Accion.ACTIVAR)

    if not maquina.esta_activo():
        return Resultado(Accion.IGNORAR)

    if maquina.estado is Estado.CONFIRMANDO:
        opcion = _detectar_opcion(texto)
        if opcion is not None:
            return Resultado(Accion.CONFIRMAR, lugar=maquina.ultimo_lugar, opcion=opcion)

        # Si en vez de una opción dice el nombre de OTRO sitio, se
        # interpreta como que cambió de opinión y se vuelve a preguntar
        # por el sitio nuevo, en vez de quedar atascado repitiendo
        # NO_ENTIENDE para siempre (confirmado en la Pi real: el usuario
        # repetía el nombre del sitio pensando que así reintentaba).
        lugar_nuevo = buscar_lugar(texto)
        if lugar_nuevo is not None:
            return Resultado(Accion.PREGUNTAR_OPCION, lugar=lugar_nuevo)

        return Resultado(Accion.NO_ENTIENDE)

    lugar = buscar_lugar(texto)
    if lugar is not None:
        return Resultado(Accion.PREGUNTAR_OPCION, lugar=lugar)

    return Resultado(Accion.NO_ENTIENDE)
