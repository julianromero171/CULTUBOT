"""
Captura audio del micrófono, lo pasa por Vosk (STT, con gramática
restringida para mejorar precisión — ver core/vocabulario.py) y despacha
cada frase reconocida al pipeline normalizar -> interpretar -> ejecutar.
"""

from __future__ import annotations

import json
import queue
from math import gcd

import numpy as np
import sounddevice as sd
from vosk import KaldiRecognizer, Model

from core.acciones import Ejecutor
from core.audio import buscar_dispositivo_entrada
from core.comandos import Accion, interpretar
from core.estados import MaquinaEstados
from core.normalizador import normalizar
from core.systemd_watchdog import WatchdogSystemd
from core.vocabulario import construir_gramatica

# Vosk trabaja mejor a 16000 Hz (los modelos estan entrenados a esa tasa).
# Los micros USB baratos capturan a 44100/48000 nativo. Se captura a la
# tasa del mic y se resamplea a 16000 en el MAIN LOOP (no en el callback
# de PortAudio, que debe ser instantaneo para no perder audio).
TASA_VOSK = 16000

BLOQUE = 8000

# Si no llega NADA del microfono en este tiempo, algo esta mal (ni una
# pausa larga hablando dura tanto) -- probablemente el stream de
# PortAudio murio silenciosamente (confirmado en la Pi real: el thread
# de audio dejo de funcionar sin ningun error visible, ni overflows
# reportados, nada). En vez de quedar colgado para siempre, se asume
# que el stream murio y se deja que el proceso termine con error, para
# que systemd (Restart=always en deploy/cultubot.service) lo reinicie
# solo -- mejor que el robot se reinicie a que se quede mudo y sordo
# sin que nadie lo note.
TIMEOUT_SIN_AUDIO_SEGUNDOS = 10.0

try:
    from scipy.signal import resample_poly
    _RESAMPLE_METODO = "scipy"
except ImportError:
    resample_poly = None
    _RESAMPLE_METODO = "numpy"


def _resample_a_16000(audio_bytes: bytes, tasa_entrada: int) -> bytes:
    """Convierte audio (int16 mono) de tasa_entrada Hz a 16000 Hz para Vosk."""
    if tasa_entrada == TASA_VOSK:
        return audio_bytes

    audio = np.frombuffer(audio_bytes, dtype=np.int16)

    if _RESAMPLE_METODO == "scipy":
        g = gcd(tasa_entrada, TASA_VOSK)
        up = TASA_VOSK // g
        down = tasa_entrada // g
        resampled = resample_poly(audio.astype(np.float32), up=up, down=down)
        return resampled.astype(np.int16).tobytes()

    # Fallback numpy: interpolacion lineal (menor calidad pero sin dependencia)
    n_in = len(audio)
    n_out = int(n_in * TASA_VOSK / tasa_entrada)
    indices = np.linspace(0, n_in - 1, n_out)
    idx_low = indices.astype(np.int32)
    idx_high = np.minimum(idx_low + 1, n_in - 1)
    frac = indices - idx_low
    out = (
        audio[idx_low].astype(np.float32) * (1 - frac)
        + audio[idx_high].astype(np.float32) * frac
    )
    return out.astype(np.int16).tobytes()


class Escuchador:
    def __init__(
        self,
        ruta_modelo: str,
        maquina: MaquinaEstados,
        ejecutor: Ejecutor,
        dispositivo_mic: str = "USB",
    ) -> None:
        self._indice_mic = buscar_dispositivo_entrada(dispositivo_mic)
        self._muestreo_hz = int(sd.query_devices(self._indice_mic)["default_samplerate"])

        self._modelo = Model(ruta_modelo)
        gramatica = construir_gramatica()
        # Vosk siempre a 16000 Hz, aunque el mic capture a otra tasa.
        self._reconocedor = KaldiRecognizer(self._modelo, TASA_VOSK, gramatica)
        self._maquina = maquina
        self._ejecutor = ejecutor
        # La cola guarda bytes CRUDOS a tasa_mic. Resamplea el main loop,
        # NO el callback, para no bloquear PortAudio.
        #
        # maxsize acotado a propósito: si el main loop se atrasa aunque sea
        # un poco, una cola SIN límite crece indefinidamente y el programa
        # termina procesando audio cada vez más viejo -- nunca se recupera,
        # y deja de reconocer cualquier cosa después de un rato (confirmado
        # en la Pi real: los overflows subían sin parar hasta que dejó de
        # escuchar del todo). Con límite, el callback descarta el bloque
        # más viejo en vez de acumular atraso: siempre se procesa audio
        # reciente, aunque se pierda algo puntual.
        self._cola: queue.Queue[bytes] = queue.Queue(maxsize=10)
        # Contador de overflows para no imprimirlos dentro del callback (print
        # bloquea con el buffer de stdout y agrava el problema). El main loop
        # los reporta cada N frames procesados.
        self._overflows = 0
        self._frames_procesados = 0
        self._watchdog = WatchdogSystemd()

    def _callback_audio(self, indata, frames, time, status) -> None:
        # Este callback corre en el thread RT de PortAudio. Solo debe:
        #  1) Contar overflows si status indica alguno (NO print)
        #  2) Encolar los bytes
        # Nada mas. Nada de print, nada de resample.
        if status:
            self._overflows += 1
        if self._cola.full():
            try:
                self._cola.get_nowait()  # descarta el bloque mas viejo, no acumular atraso
            except queue.Empty:
                pass
        self._cola.put_nowait(bytes(indata))

    def escuchar(self) -> None:
        print("=" * 50)
        print("CultuBot iniciado")
        print(f"Micrófono: [{self._indice_mic}] {sd.query_devices(self._indice_mic)['name']}")
        print(f"Tasa mic: {self._muestreo_hz} Hz  ->  Vosk: {TASA_VOSK} Hz (resample: {_RESAMPLE_METODO})")
        print("Estoy escuchando...")
        print('Di "salir" para cerrar el programa.')
        print("=" * 50)

        self._watchdog.iniciar()

        with sd.RawInputStream(
            samplerate=self._muestreo_hz,
            blocksize=BLOQUE,
            dtype="int16",
            channels=1,
            device=self._indice_mic,
            callback=self._callback_audio,
        ):
            while True:
                try:
                    datos_crudos = self._cola.get(timeout=TIMEOUT_SIN_AUDIO_SEGUNDOS)
                except queue.Empty:
                    raise RuntimeError(
                        f"No llego audio del microfono en {TIMEOUT_SIN_AUDIO_SEGUNDOS:.0f}s "
                        "-- el stream de PortAudio probablemente murio. "
                        "Terminando para que systemd reinicie el servicio."
                    ) from None

                # Prueba de vida para el watchdog de systemd: si el loop se
                # cuelga en CUALQUIER punto de aqui en adelante (bafle,
                # serial, lo que sea), esta marca deja de actualizarse y
                # systemd reinicia el servicio solo (ver core/systemd_watchdog.py).
                self._watchdog.marcar_progreso()

                # Resample AQUI, en el main loop.
                datos = _resample_a_16000(datos_crudos, self._muestreo_hz)

                self._frames_procesados += 1
                # Cada 50 frames (~9 segundos), reportar overflow acumulado
                # si hay para vigilar la salud del pipeline. Si empieza a
                # subir, hay que optimizar mas.
                if self._frames_procesados % 50 == 0 and self._overflows > 0:
                    print(f"[health] overflows acumulados: {self._overflows}")

                if not self._reconocedor.AcceptWaveform(datos):
                    continue

                resultado_json = json.loads(self._reconocedor.Result())
                texto = resultado_json.get("text", "").strip().lower()

                if not texto:
                    continue

                texto = normalizar(texto)
                print("Tú dijiste:", texto)

                resultado = interpretar(texto, self._maquina)
                self._ejecutor.ejecutar(resultado, self._maquina)

                if resultado.accion is Accion.SALIR:
                    print("Cerrando CultuBot...")
                    break

        print("Programa finalizado.")
