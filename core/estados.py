"""
Máquina de estados de CultuBot.

Reemplaza las variables sueltas (ACTIVADO, ESTADO, ULTIMO_LUGAR) por una
clase con transiciones explícitas. Esto evita mutar un módulo global desde
otros archivos y deja claro qué transiciones son válidas.

Estados:
    DORMIDO          -> Robot inactivo, solo escucha la palabra de activación.
    ESPERANDO_ORDEN  -> Robot activo, esperando un comando (ej. "dibuja el malecón").
    CONFIRMANDO      -> Robot pidió confirmación antes de dibujar.
    DIBUJANDO        -> Enviando/ejecutando el G-code en la ESP32.
    NARRANDO         -> Reproduciendo audio/narración del sitio.
    FINALIZADO       -> Ciclo de dibujo+narración terminado, vuelve a ESPERANDO_ORDEN.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class Estado(Enum):
    DORMIDO = auto()
    ESPERANDO_ORDEN = auto()
    CONFIRMANDO = auto()
    DIBUJANDO = auto()
    NARRANDO = auto()
    FINALIZADO = auto()


# Transiciones permitidas: desde qué estado se puede llegar a cuáles otros.
_TRANSICIONES_VALIDAS: dict[Estado, set[Estado]] = {
    Estado.DORMIDO: {Estado.ESPERANDO_ORDEN},
    Estado.ESPERANDO_ORDEN: {Estado.CONFIRMANDO, Estado.DORMIDO},
    # Desde CONFIRMANDO se puede ir directo a NARRANDO (opción "solo audio",
    # sin pasar por DIBUJANDO) o a DIBUJANDO (opción "dibujo" / "dibujo con audio"),
    # o volver a ESPERANDO_ORDEN si el usuario no eligió una opción válida.
    # CONFIRMANDO -> CONFIRMANDO (sí mismo): el usuario dijo el nombre de
    # OTRO sitio en vez de una opción -> se vuelve a preguntar por el
    # sitio nuevo (ver core/comandos.py), sin quedar atascado.
    Estado.CONFIRMANDO: {
        Estado.DIBUJANDO,
        Estado.NARRANDO,
        Estado.ESPERANDO_ORDEN,
        Estado.CONFIRMANDO,
    },
    Estado.DIBUJANDO: {Estado.NARRANDO, Estado.FINALIZADO},
    Estado.NARRANDO: {Estado.FINALIZADO},
    Estado.FINALIZADO: {Estado.ESPERANDO_ORDEN, Estado.DORMIDO},
}


class TransicionInvalida(Exception):
    """Se intentó pasar de un estado a otro que no está permitido."""


@dataclass
class MaquinaEstados:
    """Encapsula el estado actual del robot y el último lugar solicitado.

    Se pasa por inyección de dependencia a los módulos que la necesiten
    (comandos, acciones) en vez de importar variables globales.
    """

    estado: Estado = Estado.DORMIDO
    ultimo_lugar: Optional[object] = field(default=None)  # tipo real: core.lugares.Lugar

    def transicionar(self, nuevo_estado: Estado) -> None:
        permitidos = _TRANSICIONES_VALIDAS.get(self.estado, set())
        if nuevo_estado not in permitidos:
            raise TransicionInvalida(
                f"No se puede pasar de {self.estado.name} a {nuevo_estado.name}"
            )
        self.estado = nuevo_estado

    def esta_activo(self) -> bool:
        """El robot está "despierto" en cualquier estado distinto de DORMIDO."""
        return self.estado is not Estado.DORMIDO

    def reiniciar(self) -> None:
        self.estado = Estado.DORMIDO
        self.ultimo_lugar = None

    def establecer_lugar(self, lugar: object) -> None:
        self.ultimo_lugar = lugar
