from core.lugares import LUGARES, buscar_lugar


def test_buscar_lugar_encuentra_biblioteca():
    lugar = buscar_lugar("quiero ver la biblioteca")
    assert lugar is not None
    assert lugar.clave == "biblioteca"


def test_buscar_lugar_no_encuentra_nada():
    assert buscar_lugar("no mencione ningun sitio") is None


def test_todos_los_lugares_tienen_rutas_coherentes():
    for lugar in LUGARES.values():
        assert str(lugar.ruta_gcode()).endswith(lugar.archivo_gcode)
        assert str(lugar.ruta_audio()).endswith(lugar.archivo_audio)


def test_buscar_lugar_encuentra_por_alias():
    # "cerro" es alias de "cerro de tasajero" (la clave completa) — decir
    # solo el alias también debe activar el lugar.
    lugar = buscar_lugar("quiero ver el cerro")
    assert lugar is not None
    assert lugar.clave == "cerro de tasajero"


def test_buscar_lugar_ferrocarril_por_alias_locomotora():
    lugar = buscar_lugar("dibuja la locomotora")
    assert lugar is not None
    assert lugar.clave == "ferrocarril"


def test_frases_reconocidas_incluye_clave_y_alias():
    lugar = LUGARES["templo historico"]
    assert lugar.frases_reconocidas() == ("templo historico", "templo", "historico")


def test_lugar_sin_alias_frases_reconocidas_es_solo_la_clave():
    lugar = LUGARES["cafe"]
    assert lugar.frases_reconocidas() == ("cafe",)
