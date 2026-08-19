"""
Renderiza la trayectoria de un archivo gcode a una imagen PNG, para
revisar visualmente un dibujo antes de mandarlo a la máquina real (sin
gastar papel/tiempo de máquina en un dibujo que resulte mal).

Entiende dos estilos de "pluma abajo" (traza) vs "pluma arriba" (viaje):
- Estilo láser (LightBurn/GRBL-M3): M3 = abajo, M5 = arriba.
- Estilo eje Z (plotter real, ver herramientas/convertir_gcode_laser.py):
  Z por debajo de --umbral-z = abajo, por encima = arriba.

Uso:
    python herramientas/previsualizar_gcode.py archivo.gc salida.png
    python herramientas/previsualizar_gcode.py archivo.gcode salida.png --umbral-z 2.5
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _gcode_laser import parsear_trayectorias as _parsear_trayectorias_m3m5

_RE_COORD = re.compile(r"([XYZ])(-?\d+\.?\d*)")


def _parsear_trayectorias(ruta: Path, umbral_z: float | None) -> list[list[tuple[float, float]]]:
    if umbral_z is None:
        # Estilo láser (M3/M5): usa el parseo compartido con convertir_gcode_laser.py.
        return _parsear_trayectorias_m3m5(ruta)

    # Estilo eje Z real: Z por debajo de umbral_z = pluma abajo.
    x, y = 0.0, 0.0
    pluma_abajo = False
    trayectorias: list[list[tuple[float, float]]] = []
    actual: list[tuple[float, float]] = []

    for linea in ruta.read_text(encoding="utf-8", errors="ignore").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith(";") or linea.startswith("("):
            continue

        cmd = linea.split()[0].upper() if linea.split() else ""
        if cmd not in ("G0", "G1", "G00", "G01"):
            continue

        coords = dict(_RE_COORD.findall(linea))
        x = float(coords["X"]) if "X" in coords else x
        y = float(coords["Y"]) if "Y" in coords else y
        if "Z" in coords:
            pluma_abajo = float(coords["Z"]) < umbral_z

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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gcode", type=Path)
    parser.add_argument("salida_png", type=Path)
    parser.add_argument(
        "--umbral-z",
        type=float,
        default=None,
        help="Si el gcode usa eje Z real (no M3/M5), Z por debajo de esto = pluma abajo.",
    )
    args = parser.parse_args()

    trayectorias = _parsear_trayectorias(args.gcode, args.umbral_z)

    fig, ax = plt.subplots(figsize=(6, 6))
    for trayectoria in trayectorias:
        xs, ys = zip(*trayectoria)
        ax.plot(xs, ys, "k-", linewidth=1)
    ax.set_aspect("equal")
    ax.invert_yaxis()  # coincide con como se ve dibujando sobre la mesa
    ax.set_title(args.gcode.name)
    fig.tight_layout()
    fig.savefig(args.salida_png, dpi=150)
    print(f"Guardado: {args.salida_png} ({len(trayectorias)} trazos)")


if __name__ == "__main__":
    main()
