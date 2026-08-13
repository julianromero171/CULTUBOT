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
    "biblioteca": Lugar(
        clave="biblioteca",
        nombre="Biblioteca Pública",
        archivo_gcode="biblioteca.gcode",
        archivo_audio="biblioteca.wav",
    ),
    "cerro de tasajero": Lugar(
        clave="cerro de tasajero",
        nombre="Cerro del Tasajero",
        archivo_gcode="cerro_tasajero.gcode",
        archivo_audio="cerro_tasajero.wav",
    ),
    "locomotora": Lugar(
        clave="locomotora",
        nombre="La Locomotora",
        archivo_gcode="locomotora.gcode",
        archivo_audio="locomotora.wav",
    ),
    "templo historico": Lugar(
        clave="templo historico",
        nombre="Templo Histórico",
        archivo_gcode="templo_historico.gcode",
        archivo_audio="templo_historico.wav",
    ),
    "cafe": Lugar(
        clave="cafe",
        nombre="Café",
        archivo_gcode="cafe.gcode",
        archivo_audio="cafe.wav",
    ),
}


def buscar_lugar(texto: str) -> Lugar | None:
    """Devuelve el primer Lugar cuya clave aparece dentro del texto, o None."""
    for clave, lugar in LUGARES.items():
        if clave in texto:
            return lugar
    return None
