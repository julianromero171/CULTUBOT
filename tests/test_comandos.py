from core.comandos import Accion, interpretar
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
    resultado = interpretar("dibuja la biblioteca", maquina)
    assert resultado.accion is Accion.IGNORAR


def test_reconoce_lugar_estando_activo_dibuja_directo():
    # Flujo simplificado: reconocer el sitio ya dispara Accion.DIBUJAR,
    # sin pasar por ninguna pregunta de "que opcion quieres".
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    resultado = interpretar("dibuja la biblioteca", maquina)
    assert resultado.accion is Accion.DIBUJAR
    assert resultado.lugar is not None
    assert resultado.lugar.clave == "biblioteca"


def test_reconoce_lugar_por_alias():
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    resultado = interpretar("quiero ver el cerro", maquina)
    assert resultado.accion is Accion.DIBUJAR
    assert resultado.lugar.clave == "cerro de tasajero"


def test_no_entiende_si_no_reconoce_lugar():
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    resultado = interpretar("algo random", maquina)
    assert resultado.accion is Accion.NO_ENTIENDE
