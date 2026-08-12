"""
Reproduce archivos .wav pregrabados (narraciones de cada sitio turístico).

No usamos Piper ni ningún TTS: los audios ya están grabados de antemano
(uno por lugar, ver core/lugares.py). Este módulo solo los reproduce,
reutilizando sounddevice, que el proyecto ya usa para el micrófono.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

_DTYPE_POR_ANCHO = {1: np.int8, 2: np.int16, 4: np.int32}


def buscar_dispositivo_entrada(coincidencia: str) -> int:
    """Índice del primer dispositivo de ENTRADA (micrófono) cuyo nombre
    contiene `coincidencia` (sin distinguir mayúsculas). Se usa un
    substring del nombre en vez de un índice fijo porque el índice de
    ALSA puede cambiar entre reinicios de la Raspberry Pi.

    Si no hay coincidencia, imprime los dispositivos de entrada
    disponibles y lanza SystemExit — mejor fallar ruidosamente aquí que
    silenciosamente escuchar el dispositivo equivocado.
    """
    dispositivos = sd.query_devices()
    coincidencia = coincidencia.lower()

    for indice, dispositivo in enumerate(dispositivos):
        if dispositivo["max_input_channels"] > 0 and coincidencia in dispositivo["name"].lower():
            return indice

    print(f'No se encontró ningún micrófono cuyo nombre contenga "{coincidencia}".')
    print("Dispositivos de entrada disponibles:")
    for indice, dispositivo in enumerate(dispositivos):
        if dispositivo["max_input_channels"] > 0:
            print(f"  [{indice}] {dispositivo['name']}")
    raise SystemExit(1)


class ReproductorAudio:
    def reproducir(self, ruta: str | Path, bloqueante: bool = True) -> None:
        """bloqueante=False permite que el dibujo (ESP32Serial.enviar_gcode,
        que sí bloquea) y la narración corran en paralelo: sd.play() ya
        reproduce en un hilo propio de sounddevice, así que basta con no
        esperar (sd.wait()) a que termine.
        """
        ruta = Path(ruta)

        if not ruta.exists():
            print(f"[Audio] Archivo no encontrado: {ruta}")
            return

        with wave.open(str(ruta), "rb") as wf:
            frecuencia = wf.getframerate()
            canales = wf.getnchannels()
            ancho = wf.getsampwidth()
            crudo = wf.readframes(wf.getnframes())

        dtype = _DTYPE_POR_ANCHO.get(ancho, np.int16)
        audio = np.frombuffer(crudo, dtype=dtype)
        if canales > 1:
            audio = audio.reshape(-1, canales)

        sd.play(audio, samplerate=frecuencia)
        if bloqueante:
            sd.wait()
