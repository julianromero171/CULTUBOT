"""
Simula una conversación con CultuBot escribiendo texto en vez de hablar,
sin necesitar micrófono, modelo Vosk, ni ESP32 conectada. Usa siempre
SerialConsola (modo simulado), así que el "envío de gcode" solo se
imprime en consola.

Sirve para probar de punta a punta el pipeline
normalizar -> interpretar -> ejecutar mientras no haya hardware
disponible, o para demos rápidas.

Uso:
    python herramientas/simular_conversacion.py
    (escribe frases como "cultubot", "dibuja la biblioteca", "salir" --
    al reconocer un sitio dibuja y narra directo, sin preguntar opciones)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# En consolas de Windows con codepage distinto de UTF-8, los acentos se
# ven mal (mojibake) aunque el texto esté bien. Forzamos UTF-8 en la
# salida para que las tildes se vean correctamente al probar en PC.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.acciones import Ejecutor, SerialConsola, VozConsola
from core.audio import ReproductorAudio
from core.comandos import Accion, interpretar
from core.estados import MaquinaEstados
from core.normalizador import normalizar


def main() -> None:
    maquina = MaquinaEstados()
    ejecutor = Ejecutor(voz=VozConsola(), serial=SerialConsola(), audio=ReproductorAudio())

    print("=" * 60)
    print("Simulador de conversación de CultuBot (sin mic ni ESP32)")
    print('Escribe frases como si fueras el usuario. "salir" para terminar.')
    print("=" * 60)

    while True:
        try:
            texto = input("\nTú dices: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nSimulación interrumpida.")
            break

        if not texto:
            continue

        texto = normalizar(texto)
        resultado = interpretar(texto, maquina)
        print(f"[estado antes: se procesa '{texto}']")
        ejecutor.ejecutar(resultado, maquina)
        print(f"[estado ahora: {maquina.estado.name}]")

        if resultado.accion is Accion.SALIR:
            break

    print("Simulación finalizada.")


if __name__ == "__main__":
    main()
