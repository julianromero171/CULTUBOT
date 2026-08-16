"""
Catálogo de sitios turísticos de Cúcuta que CultuBot puede dibujar y narrar.

Cada lugar tiene:
    - clave interna (identificador canónico, para diccionarios y archivos)
    - alias: frases/palabras reales alternativas que también activan el
      lugar (ej. decir solo "cerro" en vez de la frase completa). Deben
      ser PALABRAS REALES que existan en el diccionario del modelo de
      Vosk — sílabas sueltas ("ce", "to", "ca") normalmente no están en
      el diccionario y Vosk las ignora silenciosamente (mismo problema
      que tuvo "cultubot", ver core/vocabulario.py), así que no sirven
      para acelerar el reconocimiento.
    - nombre para mostrar/decir
    - archivo de gcode dentro de drawings/ (lo ejecuta la ESP32/FluidNC)
    - archivo de audio dentro de audio/ (narración pregrabada)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

RUTA_DRAWINGS = Path("drawings")
RUTA_AUDIO = Path("audio")


@dataclass(frozen=True)
class Lugar:
    clave: str
    nombre: str
    archivo_gcode: str
    archivo_audio: str
    alias: tuple[str, ...] = field(default_factory=tuple)

    def ruta_gcode(self) -> Path:
        return RUTA_DRAWINGS / self.archivo_gcode

    def ruta_audio(self) -> Path:
        return RUTA_AUDIO / self.archivo_audio

    def frases_reconocidas(self) -> tuple[str, ...]:
        """Todas las frases que activan este lugar: la clave y sus alias."""
        return (self.clave, *self.alias)


# Fuente única de verdad: agregar un sitio nuevo solo requiere una línea aquí.
LUGARES: dict[str, Lugar] = {
    "biblioteca": Lugar(
        clave="biblioteca",
        nombre="Biblioteca Pública",
        archivo_gcode="biblioteca.gcode",
        archivo_audio="biblioteca.wav",
        alias=("publica",),
    ),
    "cerro de tasajero": Lugar(
        clave="cerro de tasajero",
        nombre="Cerro del Tasajero",
        archivo_gcode="cerro_tasajero.gcode",
        archivo_audio="cerro_tasajero.wav",
        alias=("cerro",),
    ),
    "ferrocarril": Lugar(
        clave="ferrocarril",
        nombre="El Ferrocarril",
        archivo_gcode="ferrocarril.gcode",
        archivo_audio="ferrocarril.wav",
        alias=("locomotora",),
    ),
    "templo historico": Lugar(
        clave="templo historico",
        nombre="Templo Histórico",
        archivo_gcode="templo_historico.gcode",
        archivo_audio="templo_historico.wav",
        alias=("templo", "historico"),
    ),
    "cafe": Lugar(
        clave="cafe",
        nombre="Café",
        archivo_gcode="cafe.gcode",
        archivo_audio="cafe.wav",
    ),
}


def buscar_lugar(texto: str) -> Lugar | None:
    """Devuelve el primer Lugar cuya clave o alias aparece dentro del texto, o None."""
    for lugar in LUGARES.values():
        if any(frase in texto for frase in lugar.frases_reconocidas()):
            return lugar
    return None
