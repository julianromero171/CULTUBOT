"""
Convierte texto ya normalizado en una acción concreta.

Este módulo es puro: NO modifica la máquina de estados directamente.
Solo la consulta (para saber en qué estado está) y devuelve un Resultado.
Quien aplica las transiciones de estado es core/acciones.py (Ejecutor).

Flujo simplificado (sin preguntar opciones): el usuario dice el nombre
del lugar -> Accion.DIBUJAR, con el Lugar encontrado -> el Ejecutor
dibuja y narra directo. Antes había un paso intermedio de "¿dibujo,
dibujo con audio, o solo audio?", pero se quitó a pedido del usuario:
menos pasos de conversación es menos riesgo de que el reconocimiento de
voz falle justo en la pregunta y la conversación se quede sin avanzar.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import NamedTuple, Optional

from core.estados import MaquinaEstados
from core.lugares import Lugar, buscar_lugar


class Accion(Enum):
    SALIR = auto()
    ACTIVAR = auto()
    DIBUJAR = auto()  # se reconoció un lugar: dibujar y narrar directo
    NO_ENTIENDE = auto()
    IGNORAR = auto()  # el robot está dormido y no dijeron la palabra de activación


class Resultado(NamedTuple):
    accion: Accion
    lugar: Optional[Lugar] = None


def interpretar(texto: str, maquina: MaquinaEstados) -> Resultado:
    if "salir" in texto:
        return Resultado(Accion.SALIR)

    if "cultubot" in texto:
        return Resultado(Accion.ACTIVAR)

    if not maquina.esta_activo():
        return Resultado(Accion.IGNORAR)

    lugar = buscar_lugar(texto)
    if lugar is not None:
        return Resultado(Accion.DIBUJAR, lugar=lugar)

    return Resultado(Accion.NO_ENTIENDE)
