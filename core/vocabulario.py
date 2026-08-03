"""
"Entrenar" Vosk-small de verdad (ajustar los pesos del modelo con audio
nuevo) requeriría un dataset grande en español y GPU — no es viable para
este proyecto. Pero no lo necesitamos: CultuBot no entiende lenguaje
libre, solo un conjunto fijo y conocido de frases (nombres de lugares,
opciones, activación, salir).

Para ese caso, Vosk soporta "gramática restringida": en vez de dejar que
el reconocedor busque entre todo el vocabulario del español (miles de
palabras, de ahí que la versión small se equivoque tanto), le damos la
lista exacta de frases válidas y el reconocedor solo elige entre esas.
Esto mejora la precisión muchísimo para este tipo de robot de comandos,
sin cambiar el modelo ni pesar más.

Uso: KaldiRecognizer(modelo, frecuencia, construir_gramatica())
"""

from __future__ import annotations

import json

from core.lugares import LUGARES

PALABRAS_ACTIVACION = ["cultubot", "hola cultubot"]
PALABRAS_SALIR = ["salir"]
PALABRAS_OPCION = [
    "dibujo",
    "solo el dibujo",
    "dibujo con audio",
    "dibujo y audio",
    "con audio",
    "solo audio",
    "solamente audio",
    "solo el audio",
]


def construir_gramatica() -> str:
    """Arma el JSON de gramática que espera KaldiRecognizer.

    Incluye "[unk]" para que el reconocedor pueda marcar como "desconocido"
    lo que no coincide con ninguna frase, en vez de forzar una coincidencia
    falsa con la palabra permitida más parecida.
    """
    frases = set(PALABRAS_ACTIVACION + PALABRAS_SALIR + PALABRAS_OPCION)
    for lugar in LUGARES.values():
        frases.add(lugar.clave)

    frases.add("[unk]")
    return json.dumps(sorted(frases), ensure_ascii=False)
