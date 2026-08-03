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
from core.comandos import Accion, interpretar
from core.estados import MaquinaEstados
from core.normalizador import normalizar
from core.vocabulario import construir_gramatica

MUESTREO_HZ = 16000
BLOQUE = 8000


class Escuchador:
    def __init__(
        self,
        ruta_modelo: str,
        maquina: MaquinaEstados,
        ejecutor: Ejecutor,
    ) -> None:
        self._modelo = Model(ruta_modelo)
        gramatica = construir_gramatica()
        self._reconocedor = KaldiRecognizer(self._modelo, MUESTREO_HZ, gramatica)
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
        print("Estoy escuchando...")
        print('Di "salir" para cerrar el programa.')
        print("=" * 50)

        with sd.RawInputStream(
            samplerate=MUESTREO_HZ,
            blocksize=BLOQUE,
            dtype="int16",
            channels=1,
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
