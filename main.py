"""
Punto de entrada de CultuBot.

Aquí (y solo aquí) se construyen las implementaciones concretas de cada
interfaz y se inyectan en los objetos que las necesitan.

Intenta conectar con la ESP32 real por Serial. Si no la encuentra (por
ejemplo, estás probando en tu PC sin el hardware conectado), cae
automáticamente a SerialConsola para que el resto del sistema se pueda
seguir probando sin la ESP32 físicamente presente.
"""

from __future__ import annotations

import config
from core.acciones import Ejecutor, SerialConsola, VozConsola
from core.audio import ReproductorAudio
from core.estados import MaquinaEstados
from escuchar import Escuchador
from interface.esp32_serial import ErrorConexionESP32, ESP32Serial


def construir_serial():
    """Intenta conectar con la ESP32 real; si falla, usa el stub de consola."""
    serial_real = ESP32Serial(puerto=config.PUERTO_ESP32, baudios=config.BAUDIOS_ESP32)
    try:
        serial_real.conectar()
        print(f"[main] Conectado a la ESP32 en {config.PUERTO_ESP32}")
        return serial_real
    except ErrorConexionESP32 as e:
        print(f"[main] No se pudo conectar a la ESP32 ({e}).")
        print("[main] Usando modo simulado (SerialConsola) para poder seguir probando.")
        return SerialConsola()


def construir_escuchador() -> Escuchador:
    maquina = MaquinaEstados()
    voz = VozConsola()
    serial = construir_serial()
    audio = ReproductorAudio()
    ejecutor = Ejecutor(voz=voz, serial=serial, audio=audio)
    return Escuchador(config.RUTA_MODELO_VOSK, maquina, ejecutor, config.DISPOSITIVO_MIC)


def main() -> None:
    escuchador = construir_escuchador()
    escuchador.escuchar()


if __name__ == "__main__":
    main()
