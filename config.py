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

# Substring del nombre del bafle a usar (ver core.audio.buscar_dispositivo_salida).
DISPOSITIVO_BAFLE = os.environ.get("CULTUBOT_DISPOSITIVO_BAFLE", "UAC")

# Ganancia digital aplicada a todo audio reproducido (además del volumen de
# ALSA, que se controla aparte con `amixer`). 1.0 = sin cambios, 1.5 = 50%
# más fuerte, 0.5 = mitad de volumen. Con valores > 1 hay riesgo de
# distorsión (clipping) si el audio ya venía casi al máximo; se recorta
# automáticamente para no dañar el bafle, pero puede sonar "quemado".
#   PowerShell:  $env:CULTUBOT_GANANCIA_AUDIO = "1.5"
#   Bash:        export CULTUBOT_GANANCIA_AUDIO=1.5
GANANCIA_AUDIO = float(os.environ.get("CULTUBOT_GANANCIA_AUDIO", "1.0"))
