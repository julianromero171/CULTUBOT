"""
Integración mínima con el "watchdog" de systemd (protocolo sd_notify),
sin depender del paquete `systemd` de PyPI (evita tener que compilarlo
en la Raspberry Pi).

Por qué hace falta: escuchar.py ya detecta si el MICRÓFONO deja de
mandar audio (timeout de 10s), pero eso no cubre que el programa se
cuelgue en OTRO punto (reproduciendo audio por el bafle, hablando con
la ESP32 por serial, etc.) — confirmado en la Pi real corriendo como
servicio: el proceso quedaba "activo" para systemd pero mudo y sordo
para siempre, sin que nada lo detectara.

Este módulo deja que el programa le avise a systemd "sigo vivo" solo
mientras el loop principal esté progresando de verdad. Si se cuelga en
cualquier parte, deja de avisar, y systemd (con `WatchdogSec` en
deploy/cultubot.service) mata y reinicia el servicio solo.

Si no se está corriendo bajo systemd (ej. `python main.py` a mano), no
hace nada — es seguro usarlo siempre.
"""

from __future__ import annotations

import os
import socket
import threading
import time


def _sd_notify(mensaje: str) -> None:
    direccion = os.environ.get("NOTIFY_SOCKET")
    if not direccion:
        return
    if direccion.startswith("@"):
        direccion = "\0" + direccion[1:]
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        sock.connect(direccion)
        sock.sendall(mensaje.encode())
    except OSError:
        pass  # no morir por esto, el watchdog es una ayuda, no algo critico
    finally:
        sock.close()


class WatchdogSystemd:
    """Uso:
        wd = WatchdogSystemd()
        wd.iniciar()
        while True:
            ... trabajo ...
            wd.marcar_progreso()
    """

    def __init__(self, intervalo_segundos: float = 5.0, margen_maximo_segundos: float = 30.0) -> None:
        self._intervalo = intervalo_segundos
        self._margen_maximo = margen_maximo_segundos
        self._ultimo_progreso = time.monotonic()
        self._lock = threading.Lock()

    def marcar_progreso(self) -> None:
        with self._lock:
            self._ultimo_progreso = time.monotonic()

    def iniciar(self) -> None:
        if "NOTIFY_SOCKET" not in os.environ:
            return  # no corriendo bajo systemd, no hace falta el hilo
        _sd_notify("READY=1")
        hilo = threading.Thread(target=self._bucle, daemon=True)
        hilo.start()

    def _bucle(self) -> None:
        while True:
            time.sleep(self._intervalo)
            with self._lock:
                hace_cuanto = time.monotonic() - self._ultimo_progreso
            if hace_cuanto < self._margen_maximo:
                _sd_notify("WATCHDOG=1")
            # si no, no se avisa -- systemd lo va a matar y reiniciar solo
