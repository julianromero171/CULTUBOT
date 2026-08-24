"""
Catálogo de audios pregrabados para los mensajes fijos de la conversación
(bienvenida, confirmación de elección, pregunta de opción, despedida).

Mismo mecanismo que las narraciones de core/lugares.py: archivos .wav ya
grabados, sin TTS. Ejecutor (core/acciones.py) los reproduce además de
imprimir el texto por consola (VozConsola), para que el robot "hable" en
estos puntos concretos de la conversación.
"""

from __future__ import annotations

from pathlib import Path

RUTA_AUDIO = Path("audio")

BIENVENIDA = RUTA_AUDIO / "bienvenida.wav"
DESPEDIDA = RUTA_AUDIO / "despedida.wav"
PREGUNTAR_OPCION = RUTA_AUDIO / "dibujo_con_audio_o_sin_audio.wav"
NO_ENTIENDE = RUTA_AUDIO / "no_entiende.wav"

# Confirmación de "elegiste tal lugar", una por sitio (clave de core.lugares.LUGARES).
ELECCION_POR_LUGAR: dict[str, Path] = {
    "biblioteca": RUTA_AUDIO / "eleccion_biblioteca.wav",
    "cerro de tasajero": RUTA_AUDIO / "eleccion_cerro.wav",
    "ferrocarril": RUTA_AUDIO / "eleccion_ferrocarril.wav",
    "templo historico": RUTA_AUDIO / "eleccion_templo.wav",
    "cafe": RUTA_AUDIO / "eleccion_cafe.wav",
}
