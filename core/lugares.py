"""
Catálogo de sitios turísticos de Cúcuta que CultuBot puede dibujar y narrar.

Cada lugar tiene:
    - clave interna (para buscar coincidencias en el texto reconocido)
    - nombre para mostrar/decir
    - archivo de gcode dentro de drawings/ (lo ejecuta la ESP32/FluidNC)
    - archivo de audio dentro de audio/ (narración pregrabada)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

RUTA_DRAWINGS = Path("drawings")
RUTA_AUDIO = Path("audio")


@dataclass(frozen=True)
class Lugar:
    clave: str
    nombre: str
    archivo_gcode: str
    archivo_audio: str

    def ruta_gcode(self) -> Path:
        return RUTA_DRAWINGS / self.archivo_gcode

    def ruta_audio(self) -> Path:
        return RUTA_AUDIO / self.archivo_audio


# Fuente única de verdad: agregar un sitio nuevo solo requiere una línea aquí.
LUGARES: dict[str, Lugar] = {
    "malecon": Lugar(
        clave="malecon",
        nombre="Malecón de Cúcuta",
        archivo_gcode="malecon.gcode",
        archivo_audio="malecon.wav",
    ),
    "cristo rey": Lugar(
        clave="cristo rey",
        nombre="Cristo Rey",
        archivo_gcode="cristo_rey.gcode",
        archivo_audio="cristo_rey.wav",
    ),
    "biblioteca": Lugar(
        clave="biblioteca",
        nombre="Biblioteca Pública",
        archivo_gcode="biblioteca.gcode",
        archivo_audio="biblioteca.wav",
    ),
}


def buscar_lugar(texto: str) -> Lugar | None:
    """Devuelve el primer Lugar cuya clave aparece dentro del texto, o None."""
    for clave, lugar in LUGARES.items():
        if clave in texto:
            return lugar
    return None
