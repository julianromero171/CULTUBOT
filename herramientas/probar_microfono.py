"""
Diagnóstico de reconocimiento de voz en tiempo real (Vosk + micrófono USB).

Script independiente para validar el hardware de audio en la Raspberry Pi
antes de integrarlo al flujo completo de CultuBot. A diferencia de
escuchar.py (que usa gramática restringida, ver core/vocabulario.py, para
el vocabulario fijo del robot), este script usa reconocimiento LIBRE, para
poder evaluar qué tan bien transcribe Vosk cualquier frase con tu mic real.

Uso:
    python herramientas/probar_microfono.py
    python herramientas/probar_microfono.py --dispositivo "USB PnP"

Por defecto busca cualquier dispositivo de entrada cuyo nombre contenga
"USB" (coincide con "USB PnP Sound Device" en ALSA). Si tu Raspberry Pi
tiene más de un micrófono USB, o el nombre no coincide, el script lista
todos los dispositivos disponibles para que elijas el substring correcto.
"""

from __future__ import annotations

import argparse
import json
import queue
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import sounddevice as sd
from vosk import KaldiRecognizer, Model

import config

MUESTREO_HZ = 16000
BLOQUE = 8000


def _buscar_dispositivo_entrada(coincidencia: str) -> int:
    """Índice del primer dispositivo de ENTRADA cuyo nombre contiene
    `coincidencia` (sin distinguir mayúsculas). Si no hay coincidencia,
    imprime la lista completa de entradas disponibles y termina.
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dispositivo",
        default="USB",
        help='Substring del nombre del micrófono (default: "USB"). Usar un '
        "substring en vez del índice numérico evita romperse si el índice "
        "cambia entre reinicios de la Raspberry Pi.",
    )
    args = parser.parse_args()

    indice_mic = _buscar_dispositivo_entrada(args.dispositivo)
    print(f"Usando micrófono: [{indice_mic}] {sd.query_devices(indice_mic)['name']}")

    modelo = Model(config.RUTA_MODELO_VOSK)
    reconocedor = KaldiRecognizer(modelo, MUESTREO_HZ)  # sin gramática: reconocimiento libre

    cola: queue.Queue[bytes] = queue.Queue()

    def callback(indata, frames, time, status) -> None:
        if status:
            print(status, file=sys.stderr)
        cola.put(bytes(indata))

    print("=" * 50)
    print("Escuchando... (Ctrl+C para salir)")
    print("=" * 50)

    with sd.RawInputStream(
        samplerate=MUESTREO_HZ,
        blocksize=BLOQUE,
        dtype="int16",
        channels=1,
        device=indice_mic,
        callback=callback,
    ):
        try:
            while True:
                datos = cola.get()
                if reconocedor.AcceptWaveform(datos):
                    resultado = json.loads(reconocedor.Result())
                    texto = resultado.get("text", "").strip()
                    if texto:
                        print(f"Transcripción: {texto}")
                else:
                    parcial = json.loads(reconocedor.PartialResult())
                    texto_parcial = parcial.get("partial", "").strip()
                    if texto_parcial:
                        print(f"  (parcial: {texto_parcial})", end="\r")
        except KeyboardInterrupt:
            print("\nFinalizado.")


if __name__ == "__main__":
    main()
