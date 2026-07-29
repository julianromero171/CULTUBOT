import queue
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from core.acciones import ejecutar

from core.normalizador import normalizar
from core.comandos import interpretar

# Cargar modelo
modelo = Model("models/vosk-model-small-es-0.42")

# Cola de audio
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

# Reconocedor
recognizer = KaldiRecognizer(modelo, 16000)

print("=" * 50)
print("CultuBot iniciado")
print("Estoy escuchando...")
print('Di "salir" para cerrar el programa.')
print("=" * 50)

with sd.RawInputStream(
    samplerate=16000,
    blocksize=8000,
    dtype="int16",
    channels=1,
    callback=callback
):

    while True:

        data = q.get()

        if recognizer.AcceptWaveform(data):

            resultado = json.loads(recognizer.Result())
            texto = resultado.get("text", "").strip().lower()

            if texto != "":

                texto = normalizar(texto)

                print("Tú dijiste:", texto)

                accion, datos = interpretar(texto)

                ejecutar(accion, datos)

                if accion == "SALIR":
                    print("Cerrando CultuBot...")
                    break

print("Programa finalizado.")