import pytest

from core.estados import Estado, MaquinaEstados, TransicionInvalida


def test_estado_inicial_es_dormido():
    maquina = MaquinaEstados()
    assert maquina.estado is Estado.DORMIDO
    assert not maquina.esta_activo()


def test_transicion_valida():
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    assert maquina.estado is Estado.ESPERANDO_ORDEN
    assert maquina.esta_activo()


def test_transicion_invalida_lanza_excepcion():
    maquina = MaquinaEstados()
    with pytest.raises(TransicionInvalida):
        maquina.transicionar(Estado.DIBUJANDO)


def test_flujo_completo_dibujo_con_audio():
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    maquina.transicionar(Estado.CONFIRMANDO)
    maquina.transicionar(Estado.DIBUJANDO)
    maquina.transicionar(Estado.NARRANDO)
    maquina.transicionar(Estado.FINALIZADO)
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    assert maquina.estado is Estado.ESPERANDO_ORDEN


def test_flujo_solo_audio_salta_dibujando():
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    maquina.transicionar(Estado.CONFIRMANDO)
    maquina.transicionar(Estado.NARRANDO)
    assert maquina.estado is Estado.NARRANDO


def test_confirmando_puede_reentrar_a_confirmando_con_otro_sitio():
    # Permite volver a preguntar la opción si el usuario dice el nombre
    # de otro sitio mientras ya estaba en CONFIRMANDO (ver core/comandos.py).
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    maquina.transicionar(Estado.CONFIRMANDO)
    maquina.transicionar(Estado.CONFIRMANDO)
    assert maquina.estado is Estado.CONFIRMANDO


def test_reiniciar_vuelve_a_dormido_y_limpia_lugar():
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    maquina.establecer_lugar(object())
    maquina.reiniciar()
    assert maquina.estado is Estado.DORMIDO
    assert maquina.ultimo_lugar is None
