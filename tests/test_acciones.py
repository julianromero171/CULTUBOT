from pathlib import Path

from core import mensajes
from core.acciones import Ejecutor
from core.comandos import Accion, Resultado
from core.estados import Estado, MaquinaEstados
from core.lugares import LUGARES


class FakeVoz:
    def __init__(self) -> None:
        self.mensajes: list[str] = []

    def hablar(self, texto: str) -> None:
        self.mensajes.append(texto)


class FakeSerial:
    def __init__(self, exito: bool = True) -> None:
        self.exito = exito
        self.rutas_enviadas: list[str] = []

    def enviar_gcode(self, ruta_archivo) -> bool:
        self.rutas_enviadas.append(str(ruta_archivo))
        return self.exito


class FakeAudio:
    def __init__(self) -> None:
        self.rutas_reproducidas: list[str] = []

    def reproducir(self, ruta) -> None:
        self.rutas_reproducidas.append(str(ruta))


def _construir(exito_serial: bool = True):
    voz = FakeVoz()
    serial = FakeSerial(exito=exito_serial)
    audio = FakeAudio()
    ejecutor = Ejecutor(voz=voz, serial=serial, audio=audio)
    return ejecutor, voz, serial, audio


def test_activar_transiciona_a_esperando_orden():
    ejecutor, voz, _, audio = _construir()
    maquina = MaquinaEstados()

    ejecutor.ejecutar(Resultado(Accion.ACTIVAR), maquina)

    assert maquina.estado is Estado.ESPERANDO_ORDEN
    assert any("ayudarte" in m for m in voz.mensajes)
    assert audio.rutas_reproducidas == [str(mensajes.BIENVENIDA)]


def test_dibujar_hace_todo_de_una_sin_preguntar_opciones():
    # Flujo simplificado: reconocer el sitio ya dibuja Y narra, sin
    # preguntar nada -- no hay paso intermedio de CONFIRMANDO esperando
    # una respuesta del usuario.
    ejecutor, voz, serial, audio = _construir()
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    lugar = LUGARES["biblioteca"]

    ejecutor.ejecutar(Resultado(Accion.DIBUJAR, lugar=lugar), maquina)

    assert maquina.estado is Estado.ESPERANDO_ORDEN
    assert maquina.ultimo_lugar is lugar
    assert serial.rutas_enviadas == [str(lugar.ruta_gcode())]
    assert audio.rutas_reproducidas == [
        str(mensajes.ELECCION_POR_LUGAR[lugar.clave]),
        str(lugar.ruta_audio()),
    ]
    assert any(lugar.nombre in m for m in voz.mensajes)


def test_dibujar_sin_audio_de_eleccion_igual_dibuja_y_narra(monkeypatch):
    # Todos los lugares del catálogo tienen audio de elección, pero si en
    # el futuro se agrega uno sin ELECCION_POR_LUGAR, no debe romperse.
    ejecutor, _, serial, audio = _construir()
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    lugar = LUGARES["biblioteca"]
    monkeypatch.delitem(mensajes.ELECCION_POR_LUGAR, lugar.clave)

    ejecutor.ejecutar(Resultado(Accion.DIBUJAR, lugar=lugar), maquina)

    assert serial.rutas_enviadas == [str(lugar.ruta_gcode())]
    assert audio.rutas_reproducidas == [str(lugar.ruta_audio())]


def test_dibujar_avisa_si_falla_el_envio_de_gcode_pero_igual_narra():
    ejecutor, voz, serial, audio = _construir(exito_serial=False)
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)
    lugar = LUGARES["biblioteca"]

    ejecutor.ejecutar(Resultado(Accion.DIBUJAR, lugar=lugar), maquina)

    assert any("problema" in m.lower() for m in voz.mensajes)
    # el fallo del gcode no impide que igual se reproduzca la narración
    assert audio.rutas_reproducidas[-1] == str(lugar.ruta_audio())


def test_salir_reinicia_la_maquina():
    ejecutor, voz, _, audio = _construir()
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)

    ejecutor.ejecutar(Resultado(Accion.SALIR), maquina)

    assert maquina.estado is Estado.DORMIDO
    assert any("luego" in m.lower() for m in voz.mensajes)
    assert audio.rutas_reproducidas == [str(mensajes.DESPEDIDA)]


def test_no_entiende_no_cambia_estado():
    ejecutor, voz, _, audio = _construir()
    maquina = MaquinaEstados()
    maquina.transicionar(Estado.ESPERANDO_ORDEN)

    ejecutor.ejecutar(Resultado(Accion.NO_ENTIENDE), maquina)

    assert maquina.estado is Estado.ESPERANDO_ORDEN
    assert any("no entend" in m.lower() for m in voz.mensajes)
    assert audio.rutas_reproducidas == [str(mensajes.NO_ENTIENDE)]


def test_ignorar_no_hace_nada():
    ejecutor, voz, serial, audio = _construir()
    maquina = MaquinaEstados()

    ejecutor.ejecutar(Resultado(Accion.IGNORAR), maquina)

    assert maquina.estado is Estado.DORMIDO
    assert voz.mensajes == []
    assert serial.rutas_enviadas == []
    assert audio.rutas_reproducidas == []
