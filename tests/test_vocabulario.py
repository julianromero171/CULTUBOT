import json

from core.lugares import LUGARES
from core.vocabulario import construir_gramatica


def test_gramatica_incluye_todos_los_lugares():
    frases = json.loads(construir_gramatica())
    for lugar in LUGARES.values():
        assert lugar.clave in frases


def test_gramatica_incluye_los_alias_de_los_lugares():
    frases = json.loads(construir_gramatica())
    for lugar in LUGARES.values():
        for alias in lugar.alias:
            assert alias in frases


def test_gramatica_incluye_unk():
    frases = json.loads(construir_gramatica())
    assert "[unk]" in frases


def test_gramatica_incluye_activacion_y_salir():
    # "cultubot" no está en el diccionario del modelo de Vosk (nombre
    # inventado); la gramática usa "cultura"/"culto", que sí existen, y
    # core/normalizador.py las convierte a "cultubot" antes de interpretar.
    frases = json.loads(construir_gramatica())
    assert "cultura" in frases
    assert "culto" in frases
    assert "salir" in frases
