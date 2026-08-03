"""
Revisa los archivos .gcode de drawings/ sin necesitar la ESP32 física:

- Compara drawings/ contra el catálogo real de core/lugares.py y avisa
  cuáles archivos siguen faltando.
- Para los que sí existen: cuenta líneas útiles (con el mismo filtro de
  comentarios que usa interface/esp32_serial.py, así lo que se valida
  aquí es exactamente lo que se enviaría de verdad), y revisa señales de
  alerta comunes (sin unidades G21/G20, sin modo de coordenadas G90/G91,
  paréntesis desbalanceados, líneas muy largas, caracteres no-ASCII).

No valida que el gcode sea "correcto" en el sentido de que FluidNC lo
vaya a ejecutar sin error — eso solo se puede confirmar con la ESP32
real. Es un chequeo de sanidad rápido para detectar archivos vacíos,
mal copiados, o con typos evidentes antes de tener hardware.

Uso:
    python herramientas/validar_gcode.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.lugares import LUGARES
from interface.esp32_serial import es_linea_util

LARGO_LINEA_SOSPECHOSO = 100


def _advertencias_de_contenido(lineas_utiles: list[str]) -> list[str]:
    advertencias = []

    mayus = [linea.upper() for linea in lineas_utiles]
    if not any(linea.startswith("G21") or linea.startswith("G20") for linea in mayus):
        advertencias.append("no se encontró G21 (mm) ni G20 (pulgadas) — ¿unidades definidas?")
    if not any(linea.startswith("G90") or linea.startswith("G91") for linea in mayus):
        advertencias.append("no se encontró G90 (absoluto) ni G91 (relativo) — ¿modo de coordenadas definido?")

    for i, linea in enumerate(lineas_utiles, start=1):
        if linea.count("(") != linea.count(")"):
            advertencias.append(f"línea {i}: paréntesis desbalanceados: {linea!r}")
        if len(linea) > LARGO_LINEA_SOSPECHOSO:
            advertencias.append(f"línea {i}: muy larga ({len(linea)} caracteres)")
        if not linea.isascii():
            advertencias.append(f"línea {i}: contiene caracteres no-ASCII: {linea!r}")

    return advertencias


def validar_archivo(ruta: Path) -> bool:
    """Devuelve True si el archivo existe y no tiene problemas bloqueantes."""
    if not ruta.exists():
        print(f"  FALTA: {ruta}")
        return False

    lineas_crudas = ruta.read_text(encoding="utf-8").splitlines()
    lineas_utiles = [linea.strip() for linea in lineas_crudas if es_linea_util(linea)]

    print(f"  OK: {ruta} — {len(lineas_crudas)} líneas totales, {len(lineas_utiles)} útiles")

    if not lineas_utiles:
        print("    ADVERTENCIA: no tiene ninguna línea útil (¿archivo vacío o solo comentarios?)")
        return False

    for advertencia in _advertencias_de_contenido(lineas_utiles):
        print(f"    ADVERTENCIA: {advertencia}")

    return True


def main() -> int:
    print("Validando gcode en drawings/ contra el catálogo de core/lugares.py")
    print("=" * 70)

    todo_bien = True
    for lugar in LUGARES.values():
        print(f"\n{lugar.nombre} ({lugar.clave}):")
        if not validar_archivo(lugar.ruta_gcode()):
            todo_bien = False

    print("\n" + "=" * 70)
    if todo_bien:
        print("Todos los archivos están presentes y pasaron los chequeos básicos.")
    else:
        print("Faltan archivos o hay advertencias — revisa el detalle arriba.")

    return 0 if todo_bien else 1


if __name__ == "__main__":
    raise SystemExit(main())
