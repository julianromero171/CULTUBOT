"""
Prueba el protocolo real de ESP32Serial (envío línea por línea, filtrado
de comentarios, detección de "error", timeout) sin necesitar una ESP32
física conectada: se le inyecta un transporte falso en memoria en vez
del serial.Serial real (ver interface/esp32_serial.py:conectar).

Nota: enviar_gcode() ahora manda "$X" (desbloqueo de alarma) antes de
cada archivo (ver _desbloquear), así que las listas de respuestas de
FakeTransporte incluyen una respuesta extra al principio para esa
línea, y las aserciones de `escrituras` empiezan con "$X\n".
"""

from interface.esp32_serial import ESP32Serial


class FakeTransporte:
    """Sustituto de serial.Serial: entrega una respuesta por cada write()."""

    def __init__(self, respuestas: list[bytes]) -> None:
        self._respuestas = list(respuestas)
        self.escrituras: list[str] = []
        self.is_open = True

    def write(self, datos: bytes) -> None:
        self.escrituras.append(datos.decode("utf-8"))

    def readline(self) -> bytes:
        if not self._respuestas:
            return b""  # timeout: pyserial devuelve vacío, no lanza excepción
        return self._respuestas.pop(0)

    def reset_input_buffer(self) -> None:
        pass


def _escribir_gcode(tmp_path, contenido: str):
    ruta = tmp_path / "prueba.gcode"
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def test_envia_todas_las_lineas_y_devuelve_true(tmp_path):
    ruta = _escribir_gcode(tmp_path, "G21\nG90\nG0 X0 Y0\n")
    transporte = FakeTransporte([b"ok\n", b"ok\n", b"ok\n", b"ok\n"])
    esp = ESP32Serial(transporte=transporte)

    assert esp.enviar_gcode(ruta) is True
    assert transporte.escrituras == ["$X\n", "G21\n", "G90\n", "G0 X0 Y0\n"]


def test_filtra_comentarios_de_gcode(tmp_path):
    ruta = _escribir_gcode(
        tmp_path,
        "; esto es un comentario\nG21\n(otro comentario)\nG90\n",
    )
    transporte = FakeTransporte([b"ok\n", b"ok\n", b"ok\n"])
    esp = ESP32Serial(transporte=transporte)

    assert esp.enviar_gcode(ruta) is True
    assert transporte.escrituras == ["$X\n", "G21\n", "G90\n"]


def test_detiene_el_envio_si_la_esp32_responde_error(tmp_path):
    ruta = _escribir_gcode(tmp_path, "G21\nG90\nG0 X999 Y999\n")
    transporte = FakeTransporte([b"ok\n", b"ok\n", b"error:9\n"])
    esp = ESP32Serial(transporte=transporte)

    assert esp.enviar_gcode(ruta) is False
    # Se detiene apenas ve el error, no manda la tercera línea.
    assert transporte.escrituras == ["$X\n", "G21\n", "G90\n"]


def test_manda_desbloqueo_antes_de_cada_envio(tmp_path):
    # $X se manda en CADA enviar_gcode(), no solo la primera vez -- para
    # recuperarse de una alarma que se dispare a mitad de sesión, sin
    # necesitar reconectar.
    ruta = _escribir_gcode(tmp_path, "G21\n")
    transporte = FakeTransporte([b"ok\n", b"ok\n", b"ok\n", b"ok\n"])
    esp = ESP32Serial(transporte=transporte)

    esp.enviar_gcode(ruta)
    esp.enviar_gcode(ruta)

    assert transporte.escrituras == ["$X\n", "G21\n", "$X\n", "G21\n"]


def test_timeout_sin_respuesta_devuelve_false(tmp_path):
    ruta = _escribir_gcode(tmp_path, "G21\n")
    transporte = FakeTransporte([])  # nunca responde
    esp = ESP32Serial(transporte=transporte)

    assert esp.enviar_gcode(ruta) is False


def test_archivo_inexistente_devuelve_false_sin_escribir(tmp_path):
    transporte = FakeTransporte([b"ok\n"])
    esp = ESP32Serial(transporte=transporte)

    assert esp.enviar_gcode(tmp_path / "no_existe.gcode") is False
    assert transporte.escrituras == []
