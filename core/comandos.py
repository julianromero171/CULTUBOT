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


# Frases reconocidas por opción, de más específica a menos específica.
_FRASES_OPCION: list[tuple[str, Opcion]] = [
    ("dibujo con audio", Opcion.DIBUJO_CON_AUDIO),
    ("dibujo y audio", Opcion.DIBUJO_CON_AUDIO),
    ("con audio", Opcion.DIBUJO_CON_AUDIO),
    ("solo audio", Opcion.SOLO_AUDIO),
    ("solamente audio", Opcion.SOLO_AUDIO),
    ("solo el audio", Opcion.SOLO_AUDIO),
    ("dibujo", Opcion.DIBUJO),
    ("solo el dibujo", Opcion.DIBUJO),
]


class Resultado(NamedTuple):
    accion: Accion
    lugar: Optional[Lugar] = None
    opcion: Optional[Opcion] = None


def _detectar_opcion(texto: str) -> Optional[Opcion]:
    for frase, opcion in _FRASES_OPCION:
        if frase in texto:
            return opcion
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
        if opcion is None:
            return Resultado(Accion.NO_ENTIENDE)
        return Resultado(Accion.CONFIRMAR, lugar=maquina.ultimo_lugar, opcion=opcion)

    lugar = buscar_lugar(texto)
    if lugar is not None:
        return Resultado(Accion.PREGUNTAR_OPCION, lugar=lugar)

    return Resultado(Accion.NO_ENTIENDE)
