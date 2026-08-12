"""
Captura audio del micrófono, lo pasa por Vosk (STT, con gramática
restringida para mejorar precisión — ver core/vocabulario.py) y despacha
cada frase reconocida al pipeline normalizar -> interpretar -> ejecutar.
"""

from __future__ import annotations

import json
import queue

import sounddevice as sd
from vosk import KaldiRecognizer, Model

from core.acciones import Ejecutor
from core.audio import buscar_dispositivo_entrada
from core.comandos import Accion, interpretar
from core.estados import MaquinaEstados
from core.normalizador import normalizar
from core.vocabulario import construir_gramatica

BLOQUE = 8000


class Escuchador:
    def __init__(
        self,
        ruta_modelo: str,
        maquina: MaquinaEstados,
        ejecutor: Ejecutor,
        dispositivo_mic: str = "USB",
    ) -> None:
        # Muchos micrófonos USB baratos no soportan 16000 Hz de forma
        # nativa (solo 44100/48000). Se detecta el dispositivo por nombre
        # y se usa la tasa que él mismo reporta, en vez de forzar 16000,
        # para no chocar con PortAudioError: Invalid sample rate.
        self._indice_mic = buscar_dispositivo_entrada(dispositivo_mic)
        self._muestreo_hz = int(sd.query_devices(self._indice_mic)["default_samplerate"])

        self._modelo = Model(ruta_modelo)
        gramatica = construir_gramatica()
        self._reconocedor = KaldiRecognizer(self._modelo, self._muestreo_hz, gramatica)
        self._maquina = maquina
        self._ejecutor = ejecutor
        self._cola: queue.Queue[bytes] = queue.Queue()

    def _callback_audio(self, indata, frames, time, status) -> None:
        if status:
            print(status)
        self._cola.put(bytes(indata))

    def escuchar(self) -> None:
        print("=" * 50)
        print("CultuBot iniciado")
        print(f"Micrófono: [{self._indice_mic}] {sd.query_devices(self._indice_mic)['name']}")
        print(f"Tasa de muestreo: {self._muestreo_hz} Hz")
        print("Estoy escuchando...")
        print('Di "salir" para cerrar el programa.')
        print("=" * 50)

        with sd.RawInputStream(
            samplerate=self._muestreo_hz,
            blocksize=BLOQUE,
            dtype="int16",
            channels=1,
            device=self._indice_mic,
            callback=self._callback_audio,
        ):
            while True:
                datos = self._cola.get()

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
