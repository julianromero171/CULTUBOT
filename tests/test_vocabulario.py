import json

from core.lugares import LUGARES
from core.vocabulario import construir_gramatica


def test_gramatica_incluye_todos_los_lugares():
    frases = json.loads(construir_gramatica())
    for lugar in LUGARES.values():
        assert lugar.clave in frases


def test_gramatica_incluye_unk():
    frases = json.loads(construir_gramatica())
    assert "[unk]" in frases


def test_gramatica_incluye_activacion_y_salir():
    frases = json.loads(construir_gramatica())
    assert "cultubot" in frases
    assert "salir" in frases
