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


def test_gramatica_incluye_las_palabras_clave_de_opcion():
    # core/comandos.py (_detectar_opcion) solo busca estas dos palabras
    # sueltas, no una frase completa -- tienen que estar en la gramática.
    frases = json.loads(construir_gramatica())
    assert "dibujo" in frases
    assert "audio" in frases
