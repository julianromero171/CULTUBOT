"""
Ejecuta la acción decidida por core/comandos.py y aplica la transición de
estado correspondiente en la MaquinaEstados.

Diseño: Ejecutor recibe por inyección de dependencia:
    - una interfaz de voz (InterfazVoz)          -> mensajes cortos del sistema
    - un reproductor de audio (ReproductorAudio) -> narraciones .wav pregrabadas
    - una interfaz serial (InterfazSerial)       -> streaming de gcode a la ESP32

VozConsola sigue siendo un stub de texto (no usamos Piper). InterfazSerial
ahora normalmente es interface.esp32_serial.ESP32Serial (real), pero se
puede seguir usando SerialConsola para probar en el PC sin la ESP32
conectada — el resto del código no cambia, solo lo que se inyecta en
main.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from core import mensajes
from core.audio import ReproductorAudio
from core.comandos import Accion, Opcion, Resultado
from core.estados import Estado, MaquinaEstados
from core.lugares import Lugar


class InterfazVoz(Protocol):
    def hablar(self, texto: str) -> None: ...


class InterfazSerial(Protocol):
    def enviar_gcode(self, ruta_archivo: str | Path) -> bool: ...


class VozConsola:
    """Mensajes cortos del sistema (no la narración, esa va por audio real)."""

    def hablar(self, texto: str) -> None:
        print(f"[CultuBot dice]: {texto}")


class SerialConsola:
    """Stub para probar en PC sin la ESP32 conectada. Siempre 'tiene éxito'."""

    def enviar_gcode(self, ruta_archivo: str | Path) -> bool:
        print(f"[Serial simulado] enviaría el archivo: {ruta_archivo}")
        return True


class Ejecutor:
    def __init__(
        self,
        voz: InterfazVoz,
        serial: InterfazSerial,
        audio: ReproductorAudio | None = None,
    ) -> None:
        self._voz = voz
        self._serial = serial
        self._audio = audio or ReproductorAudio()

    def ejecutar(self, resultado: Resultado, maquina: MaquinaEstados) -> None:
        manejador = {
            Accion.ACTIVAR: self._activar,
            Accion.PREGUNTAR_OPCION: self._preguntar_opcion,
            Accion.CONFIRMAR: self._confirmar,
            Accion.SALIR: self._salir,
            Accion.NO_ENTIENDE: self._no_entiende,
            Accion.IGNORAR: self._ignorar,
        }[resultado.accion]
        manejador(resultado, maquina)

    def _activar(self, resultado: Resultado, maquina: MaquinaEstados) -> None:
        if maquina.estado is Estado.DORMIDO:
            maquina.transicionar(Estado.ESPERANDO_ORDEN)
        self._voz.hablar("Hola, ¿en qué puedo ayudarte?")
        self._audio.reproducir(mensajes.BIENVENIDA)

    def _preguntar_opcion(self, resultado: Resultado, maquina: MaquinaEstados) -> None:
        lugar = resultado.lugar
        assert lugar is not None

        maquina.establecer_lugar(lugar)
        maquina.transicionar(Estado.CONFIRMANDO)
        self._voz.hablar(
            f"Encontré {lugar.nombre}. "
            "¿Quieres el dibujo, dibujo con audio, o solo audio?"
        )

        ruta_eleccion = mensajes.ELECCION_POR_LUGAR.get(lugar.clave)
        if ruta_eleccion is not None:
            self._audio.reproducir(ruta_eleccion)
        self._audio.reproducir(mensajes.PREGUNTAR_OPCION)

    def _confirmar(self, resultado: Resultado, maquina: MaquinaEstados) -> None:
        lugar: Lugar | None = maquina.ultimo_lugar
        if lugar is None or resultado.opcion is None:
            self._no_entiende(resultado, maquina)
            return

        if resultado.opcion is Opcion.DIBUJO:
            self._hacer_dibujo(lugar, maquina)

        elif resultado.opcion is Opcion.DIBUJO_CON_AUDIO:
            self._hacer_dibujo(lugar, maquina)
            self._hacer_narracion(lugar, maquina)

        elif resultado.opcion is Opcion.SOLO_AUDIO:
            maquina.transicionar(Estado.NARRANDO)
            self._voz.hablar(f"Reproduciendo la narración de {lugar.nombre}.")
            self._audio.reproducir(lugar.ruta_audio())

        maquina.transicionar(Estado.FINALIZADO)
        maquina.transicionar(Estado.ESPERANDO_ORDEN)

    def _hacer_dibujo(self, lugar: Lugar, maquina: MaquinaEstados) -> None:
        maquina.transicionar(Estado.DIBUJANDO)
        self._voz.hablar(f"Preparando el dibujo de {lugar.nombre}.")

        exito = self._serial.enviar_gcode(lugar.ruta_gcode())
        if not exito:
            self._voz.hablar(
                "Hubo un problema enviando el dibujo a la máquina. "
                "Revisa la conexión con la ESP32."
            )

    def _hacer_narracion(self, lugar: Lugar, maquina: MaquinaEstados) -> None:
        maquina.transicionar(Estado.NARRANDO)
        self._voz.hablar(f"Este es {lugar.nombre}.")
        self._audio.reproducir(lugar.ruta_audio())

    def _salir(self, resultado: Resultado, maquina: MaquinaEstados) -> None:
        self._voz.hablar("Hasta luego.")
        self._audio.reproducir(mensajes.DESPEDIDA)
        maquina.reiniciar()

    def _no_entiende(self, resultado: Resultado, maquina: MaquinaEstados) -> None:
        self._voz.hablar("Lo siento, no entendí lo que dijiste.")
        self._audio.reproducir(mensajes.NO_ENTIENDE)

    def _ignorar(self, resultado: Resultado, maquina: MaquinaEstados) -> None:
        pass
