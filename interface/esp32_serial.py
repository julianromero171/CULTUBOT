"""
Comunicación real Raspberry Pi <-> ESP32 (FluidNC) por USB Serial.

FluidNC (como Grbl) entiende G-code que le llega línea por línea por el
puerto serial, y responde "ok" cuando acepta cada línea o "error:<n>" si
algo salió mal. Este módulo implementa ese protocolo de streaming con
confirmación (send-and-wait): es el método más simple y confiable, aunque
no el más rápido posible (para máxima velocidad se podría usar streaming
con buffer tipo "character counting", pero para WRO la confiabilidad
importa más que unos milisegundos).

Este módulo vive en interface/ porque es literalmente la interfaz de
comunicación entre los dos "cerebros" del robot (Raspberry <-> ESP32).
"""

from __future__ import annotations

import time
from pathlib import Path

import serial


class ErrorConexionESP32(Exception):
    """No se pudo abrir el puerto serial hacia la ESP32."""


class ESP32Serial:
    def __init__(
        self,
        puerto: str = "/dev/ttyUSB0",
        baudios: int = 115200,
        timeout_segundos: float = 5.0,
        transporte: serial.Serial | None = None,
    ) -> None:
        """transporte: para tests, se puede inyectar un objeto compatible con
        la interfaz de serial.Serial (write/readline/reset_input_buffer/is_open)
        en vez de abrir un puerto real. Si se pasa, conectar() lo usa tal cual
        y no crea una conexión serial de verdad.
        """
        self._puerto = puerto
        self._baudios = baudios
        self._timeout = timeout_segundos
        self._conexion: serial.Serial | None = transporte
        self._transporte_inyectado = transporte is not None

    def conectar(self) -> None:
        if self._transporte_inyectado:
            return

        try:
            self._conexion = serial.Serial(
                self._puerto, self._baudios, timeout=self._timeout
            )
        except serial.SerialException as e:
            raise ErrorConexionESP32(
                f"No se pudo abrir el puerto {self._puerto}: {e}"
            ) from e

        # La ESP32 se reinicia sola al abrir el puerto serial (típico de
        # las placas con chip USB-serial). Hay que darle tiempo a que
        # FluidNC termine de arrancar antes de mandarle nada.
        time.sleep(2.0)
        self._conexion.reset_input_buffer()

    def esta_conectado(self) -> bool:
        return self._conexion is not None and self._conexion.is_open

    def _linea_es_util(self, linea: str) -> bool:
        linea = linea.strip()
        if not linea:
            return False
        if linea.startswith(";") or linea.startswith("("):
            return False  # comentarios de gcode
        return True

    def enviar_gcode(self, ruta_archivo: str | Path) -> bool:
        """Envía un archivo .gcode/.txt línea por línea.

        Devuelve True si todas las líneas fueron aceptadas ("ok"),
        False si hubo un error, timeout, o el archivo/conexión no existen.
        """
        ruta = Path(ruta_archivo)
        if not ruta.exists():
            print(f"[ESP32Serial] archivo no encontrado: {ruta}")
            return False

        if not self.esta_conectado():
            try:
                self.conectar()
            except ErrorConexionESP32 as e:
                print(f"[ESP32Serial] {e}")
                return False

        lineas = [
            linea.strip()
            for linea in ruta.read_text(encoding="utf-8").splitlines()
            if self._linea_es_util(linea)
        ]
        total = len(lineas)

        for i, linea in enumerate(lineas, start=1):
            self._conexion.write((linea + "\n").encode("utf-8"))
            respuesta = self._leer_respuesta()

            if respuesta is None:
                print(f"[ESP32Serial] timeout esperando respuesta (línea {i}/{total}: {linea})")
                return False

            if respuesta.lower().startswith("error"):
                print(f"[ESP32Serial] {respuesta} en línea {i}/{total}: {linea}")
                return False

        return True

    def _leer_respuesta(self) -> str | None:
        cruda = self._conexion.readline().decode(errors="ignore").strip()
        return cruda if cruda else None

    def cerrar(self) -> None:
        if self._conexion is not None and self._conexion.is_open:
            self._conexion.close()
