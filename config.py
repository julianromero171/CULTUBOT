"""
Configuración de CultuBot, leída de variables de entorno con los mismos
valores por defecto que antes tenía main.py hardcodeados.

Así se puede cambiar de máquina (PC de pruebas en Windows vs Raspberry Pi
real) seteando variables de entorno en vez de editar código:

    PowerShell:  $env:CULTUBOT_PUERTO_ESP32 = "COM3"
    Bash:        export CULTUBOT_PUERTO_ESP32=/dev/ttyACM0
"""

from __future__ import annotations

import os

RUTA_MODELO_VOSK = os.environ.get(
    "CULTUBOT_RUTA_MODELO_VOSK", "models/vosk-model-small-es-0.42"
)

# Linux/Raspberry Pi: normalmente "/dev/ttyUSB0" o "/dev/ttyACM0"
# Windows (solo para pruebas en PC): "COM3", "COM4", etc.
PUERTO_ESP32 = os.environ.get("CULTUBOT_PUERTO_ESP32", "/dev/ttyUSB0")

BAUDIOS_ESP32 = int(os.environ.get("CULTUBOT_BAUDIOS_ESP32", "115200"))

# Substring del nombre del micrófono a usar (ver core.audio.buscar_dispositivo_entrada).
# Sirve para no depender del índice de ALSA, que puede cambiar entre reinicios.
DISPOSITIVO_MIC = os.environ.get("CULTUBOT_DISPOSITIVO_MIC", "USB")
