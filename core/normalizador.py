"""
Corrige errores comunes de reconocimiento de voz (Vosk) antes de interpretar
el texto como comando.

Importante: las reglas se aplican en orden, de más específica (frase larga)
a menos específica (palabra corta). Si "cultura" se reemplazara antes que
"cultura bot", la frase "cultura bot" quedaría rota ("cultubot bot") porque
la subcadena "cultura" ya se habría consumido. Por eso las reglas están
ordenadas y no son un simple diccionario sin orden garantizado.
"""

from __future__ import annotations

# (patrón, reemplazo) — el orden importa: frases largas primero.
REGLAS: list[tuple[str, str]] = [
    ("cultura bot", "cultubot"),
    ("culto bot", "cultubot"),
    ("cultura", "cultubot"),
    ("culto", "cultubot"),
    ("male con", "malecon"),
    ("malecón", "malecon"),
    ("cristo rey", "cristo rey"),  # ya está bien, se deja explícito por claridad
]


def normalizar(texto: str) -> str:
    texto = texto.lower().strip()
    for patron, reemplazo in REGLAS:
        texto = texto.replace(patron, reemplazo)
    return texto
