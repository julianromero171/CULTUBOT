from core.lugares import LUGARES, buscar_lugar


def test_buscar_lugar_encuentra_malecon():
    lugar = buscar_lugar("quiero ver el malecon")
    assert lugar is not None
    assert lugar.clave == "malecon"


def test_buscar_lugar_no_encuentra_nada():
    assert buscar_lugar("no mencione ningun sitio") is None


def test_todos_los_lugares_tienen_rutas_coherentes():
    for lugar in LUGARES.values():
        assert str(lugar.ruta_gcode()).endswith(lugar.archivo_gcode)
        assert str(lugar.ruta_audio()).endswith(lugar.archivo_audio)
