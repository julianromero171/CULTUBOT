from core.comandos import Accion, Opcion, interpretar
from core.estados import Estado, MaquinaEstados


def test_salir_desde_cualquier_estado():
    maquina = MaquinaEstados()
    resultado = interpretar("salir", maquina)
    assert resultado.accion is Accion.SALIR


def test_activar_desde_dormido():
    maquina = MaquinaEstados()
    resultado = interpretar("cultubot", maquina)
    assert resultado.accion is Accion.ACTIVAR


def test_ignora_si_esta_dormido_y_no_dice_activacion():
    maquina = MaquinaEstados()
    resultado = interpretar("dibuja el malecon", maquina)
    assert resultado.accion is Accion.IGNORAR


def test_reconoce_lugar_estando_activo():
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    resultado = interpretar("dibuja el malecon", maquina)
    assert resultado.accion is Accion.PREGUNTAR_OPCION
    assert resultado.lugar is not None
    assert resultado.lugar.clave == "malecon"


def test_no_entiende_si_no_reconoce_lugar():
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    resultado = interpretar("algo random", maquina)
    assert resultado.accion is Accion.NO_ENTIENDE


def test_confirmando_detecta_opcion_dibujo_con_audio_antes_que_dibujo():
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    maquina.transicionar(Estado.CONFIRMANDO)
    resultado = interpretar("dibujo con audio", maquina)
    assert resultado.accion is Accion.CONFIRMAR
    assert resultado.opcion is Opcion.DIBUJO_CON_AUDIO


def test_confirmando_detecta_solo_dibujo():
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    maquina.transicionar(Estado.CONFIRMANDO)
    resultado = interpretar("dibujo", maquina)
    assert resultado.accion is Accion.CONFIRMAR
    assert resultado.opcion is Opcion.DIBUJO


def test_confirmando_detecta_solo_audio():
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    maquina.transicionar(Estado.CONFIRMANDO)
    resultado = interpretar("solo audio", maquina)
    assert resultado.accion is Accion.CONFIRMAR
    assert resultado.opcion is Opcion.SOLO_AUDIO


def test_confirmando_no_entiende_opcion_invalida():
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    maquina.transicionar(Estado.CONFIRMANDO)
    resultado = interpretar("no se que quiero", maquina)
    assert resultado.accion is Accion.NO_ENTIENDE
