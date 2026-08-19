"""
Convierte un gcode exportado por LightBurn en modo láser (M3/S=on,
M5=off, más M8/M9 de refrigerante) a gcode compatible con el plotter de
lápiz de CultuBot: el servo del eje Z sube/baja el lápiz en vez de
prender/apagar un láser. También reescala el dibujo para que quepa
seguro dentro del área de trabajo real de la máquina (fluidnc/config.yaml
tiene soft_limits y hard_limits desactivados, así que un gcode con
coordenadas fuera de rango puede forzar la mecánica sin ninguna
protección).

Los valores de Z (--z-abajo / --z-arriba) son de PRUEBA por defecto —
hay que calibrarlos probando físicamente cuánto debe bajar/subir el
servo para que el lápiz toque el papel sin forzar, y ajustar con estos
mismos parámetros.

Uso:
    python herramientas/convertir_gcode_laser.py entrada.gc salida.gcode
    python herramientas/convertir_gcode_laser.py entrada.gc salida.gcode --z-abajo 0 --z-arriba 8 --area 180 --margen 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _gcode_laser import bounds, parsear_trayectorias


def convertir(
    ruta_entrada: Path,
    ruta_salida: Path,
    z_abajo: float,
    z_arriba: float,
    area: float,
    margen: float,
    feed_xy: int,
    feed_z: int,
) -> None:
    trayectorias = parsear_trayectorias(ruta_entrada)
    if not trayectorias:
        raise ValueError(f"{ruta_entrada}: no se encontraron trazos (M3...M5) en el archivo")

    x_min, y_min, x_max, y_max = bounds(trayectorias)
    ancho, alto = x_max - x_min, y_max - y_min
    escala = min(area / ancho, area / alto) if ancho and alto else 1.0

    def _transformar(punto: tuple[float, float]) -> tuple[float, float]:
        x, y = punto
        return (x - x_min) * escala + margen, (y - y_min) * escala + margen

    lineas = [
        f"; Convertido desde {ruta_entrada.name} por herramientas/convertir_gcode_laser.py",
        f"; Pluma abajo=Z{z_abajo} arriba=Z{z_arriba} -- valores de PRUEBA, calibrar fisicamente",
        "G21",
        "G90",
        f"G1 Z{z_arriba} F{feed_z}",
        "G4 P0.3",
    ]

    for trazo in trayectorias:
        puntos = [_transformar(p) for p in trazo]
        x0, y0 = puntos[0]
        lineas.append(f"G0 X{x0:.2f} Y{y0:.2f}")
        lineas.append(f"G1 Z{z_abajo} F{feed_z}")
        lineas.append("G4 P0.3")
        for x, y in puntos[1:]:
            lineas.append(f"G1 X{x:.2f} Y{y:.2f} F{feed_xy}")
        lineas.append(f"G1 Z{z_arriba} F{feed_z}")
        lineas.append("G4 P0.3")

    lineas.append("G0 X0 Y0")

    ruta_salida.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(
        f"{ruta_entrada.name} -> {ruta_salida.name}: {len(trayectorias)} trazos, "
        f"original {ancho:.0f}x{alto:.0f}mm, escalado x{escala:.3f} a "
        f"{ancho*escala:.0f}x{alto*escala:.0f}mm (+{margen}mm de margen)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path)
    parser.add_argument("salida", type=Path)
    parser.add_argument("--z-abajo", type=float, default=0.0, help="Z con la pluma tocando el papel (default 0, AJUSTAR)")
    parser.add_argument("--z-arriba", type=float, default=10.0, help="Z con la pluma levantada (default 10, AJUSTAR)")
    parser.add_argument("--area", type=float, default=180.0, help="Tamaño máximo del dibujo en mm (default 180, deja margen dentro de max_travel_mm=200)")
    parser.add_argument("--margen", type=float, default=10.0, help="Offset desde el origen en mm (default 10)")
    parser.add_argument("--feed-xy", type=int, default=800, help="Velocidad F para movimientos de dibujo (default 800)")
    parser.add_argument("--feed-z", type=int, default=300, help="Velocidad F para subir/bajar la pluma (default 300)")
    args = parser.parse_args()

    convertir(
        args.entrada,
        args.salida,
        args.z_abajo,
        args.z_arriba,
        args.area,
        args.margen,
        args.feed_xy,
        args.feed_z,
    )


if __name__ == "__main__":
    main()
