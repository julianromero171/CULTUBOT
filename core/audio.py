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


def _resamplear(audio: np.ndarray, frecuencia_original: int, frecuencia_destino: int) -> np.ndarray:
    """Convierte el audio a la tasa de muestreo que el bafle sí soporta
    (interpolación lineal simple, suficiente para narración hablada). Los
    .wav reales no todos comparten la misma tasa (unos 44100 Hz, otros
    24000 Hz), y el bafle USB solo acepta la suya — hay que igualarla
    siempre, no asumir que el archivo ya viene en la tasa correcta.
    """
    if frecuencia_original == frecuencia_destino:
        return audio

    dtype_original = audio.dtype
    n_muestras_originales = audio.shape[0]
    n_muestras_destino = max(1, round(n_muestras_originales * frecuencia_destino / frecuencia_original))
    indices_originales = np.arange(n_muestras_originales)
    indices_destino = np.linspace(0, n_muestras_originales - 1, n_muestras_destino)

    if audio.ndim == 1:
        return np.interp(indices_destino, indices_originales, audio).astype(dtype_original)

    canales = [
        np.interp(indices_destino, indices_originales, audio[:, c]) for c in range(audio.shape[1])
    ]
    return np.stack(canales, axis=1).astype(dtype_original)


def _indice_dispositivo(coincidencia: str, campo_canales: str) -> int | None:
    dispositivos = sd.query_devices()
    coincidencia = coincidencia.lower()
    for indice, dispositivo in enumerate(dispositivos):
        if dispositivo[campo_canales] > 0 and coincidencia in dispositivo["name"].lower():
            return indice
    return None


def buscar_dispositivo_entrada(coincidencia: str) -> int:
    """Índice del primer dispositivo de ENTRADA (micrófono) cuyo nombre
    contiene `coincidencia` (sin distinguir mayúsculas). Se usa un
    substring del nombre en vez de un índice fijo porque el índice de
    ALSA puede cambiar entre reinicios de la Raspberry Pi.

    Si no hay coincidencia, imprime los dispositivos de entrada
    disponibles y lanza SystemExit — mejor fallar ruidosamente aquí que
    silenciosamente escuchar el dispositivo equivocado (sin mic no hay
    forma de que el robot funcione).
    """
    indice = _indice_dispositivo(coincidencia, "max_input_channels")
    if indice is not None:
        return indice

    print(f'No se encontró ningún micrófono cuyo nombre contenga "{coincidencia}".')
    print("Dispositivos de entrada disponibles:")
    for i, dispositivo in enumerate(sd.query_devices()):
        if dispositivo["max_input_channels"] > 0:
            print(f"  [{i}] {dispositivo['name']}")
    raise SystemExit(1)


def buscar_dispositivo_salida(coincidencia: str) -> int | None:
    """Índice del primer dispositivo de SALIDA (bafle) cuyo nombre contiene
    `coincidencia`. A diferencia de buscar_dispositivo_entrada, si no
    encuentra coincidencia devuelve None (cae al dispositivo de salida por
    defecto) en vez de fallar — así ReproductorAudio se puede seguir
    usando en un PC sin bafle USB (p.ej. herramientas/simular_conversacion.py).
    """
    indice = _indice_dispositivo(coincidencia, "max_output_channels")
    if indice is None:
        print(f'[Audio] No se encontró bafle cuyo nombre contenga "{coincidencia}"; usando salida por defecto.')
    return indice


class ReproductorAudio:
    def __init__(self, dispositivo: str = "UAC") -> None:
        """dispositivo: substring del nombre del bafle a usar (ver
        buscar_dispositivo_salida). Se resuelve la primera vez que se
        reproduce algo, no en el constructor, para no consultar los
        dispositivos de audio si nunca se llega a usar.
        """
        self._dispositivo = dispositivo
        self._indice_salida: int | None = None
        self._indice_resuelto = False

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

        if not self._indice_resuelto:
            self._indice_salida = buscar_dispositivo_salida(self._dispositivo)
            self._indice_resuelto = True

        with wave.open(str(ruta), "rb") as wf:
            frecuencia = wf.getframerate()
            canales = wf.getnchannels()
            ancho = wf.getsampwidth()
            crudo = wf.readframes(wf.getnframes())

        dtype = _DTYPE_POR_ANCHO.get(ancho, np.int16)
        audio = np.frombuffer(crudo, dtype=dtype)
        if canales > 1:
            audio = audio.reshape(-1, canales)

        frecuencia_reproduccion = frecuencia
        if self._indice_salida is not None:
            frecuencia_dispositivo = int(
                sd.query_devices(self._indice_salida)["default_samplerate"]
            )
            if frecuencia_dispositivo != frecuencia:
                audio = _resamplear(audio, frecuencia, frecuencia_dispositivo)
                frecuencia_reproduccion = frecuencia_dispositivo

        sd.play(audio, samplerate=frecuencia_reproduccion, device=self._indice_salida)
        if bloqueante:
            sd.wait()
