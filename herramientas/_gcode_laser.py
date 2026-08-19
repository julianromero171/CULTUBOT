"""
Lectura compartida de gcode estilo láser (LightBurn/GRBL-M3: M3=pluma
abajo, M5=pluma arriba) — usada tanto por previsualizar_gcode.py como
por convertir_gcode_laser.py para no duplicar el parseo.
"""

from __future__ import annotations

import re
from pathlib import Path

_RE_COORD = re.compile(r"([XYZ])(-?\d+\.?\d*)")


def parsear_trayectorias(ruta: Path) -> list[list[tuple[float, float]]]:
    """Devuelve una lista de trazos (cada uno, una lista de puntos X,Y)
    correspondientes a los tramos donde la pluma/láser estaba "abajo"
    (entre un M3 y el siguiente M5).
    """
    x, y = 0.0, 0.0
    pluma_abajo = False
    trayectorias: list[list[tuple[float, float]]] = []
    actual: list[tuple[float, float]] = []

    for linea in ruta.read_text(encoding="utf-8", errors="ignore").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith(";") or linea.startswith("("):
            continue

        cmd = linea.split()[0].upper() if linea.split() else ""

        if cmd == "M3":
            pluma_abajo = True
        elif cmd == "M5":
            pluma_abajo = False

        if cmd in ("G0", "G1", "G00", "G01"):
            coords = dict(_RE_COORD.findall(linea))
            x = float(coords["X"]) if "X" in coords else x
            y = float(coords["Y"]) if "Y" in coords else y

            estaba_dibujando = bool(actual)
            if pluma_abajo:
                if not estaba_dibujando:
                    actual = [(x, y)]
                    trayectorias.append(actual)
                actual.append((x, y))
            else:
                if estaba_dibujando:
                    actual = []

    return trayectorias


def bounds(trayectorias: list[list[tuple[float, float]]]) -> tuple[float, float, float, float]:
    """(x_min, y_min, x_max, y_max) de todos los puntos."""
    xs = [x for trazo in trayectorias for x, _ in trazo]
    ys = [y for trazo in trayectorias for _, y in trazo]
    return min(xs), min(ys), max(xs), max(ys)
