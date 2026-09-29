"""TSP nube (stub PENDIENTE para fase streaming: n grande sin matriz densa).

TODO estudiantes / fase 2: no construir matriz n×n; guarda solo la nube de
puntos y calcula distancias al vuelo (o por lotes con ``stream_puntos``).
``DIMENSIONES = 2`` para que ``stream_puntos`` funcione; ``enumerar`` debe
seguir fallando con ``ProblemaDemasiadoGrande`` si n > LIMITE_ENUMERACION.

Caso chico esperado: misma semántica que Viajero (tour canónico abierto,
costo con retorno, desempate <); el stub aún no resuelve nada.
"""

from __future__ import annotations

from typing import ClassVar, Iterator

from lab_bioinspirados.nucleo.problema import Problema

PENDIENTE = True


class TSPNube(Problema):
    """TODO fase 2: TSP por streaming sin matriz densa (n > 32)."""

    NOMBRE: ClassVar[str] = "tsp-nube"
    PENDIENTE: ClassVar[bool] = True
    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 2

    def __init__(self, coordenadas: object = None) -> None:
        self._coordenadas = coordenadas

    @property
    def nombre(self) -> str:
        return "TSP-nube-pendiente"

    @property
    def tamano(self) -> int:
        raise NotImplementedError("TODO fase 2: tamano = nº de puntos de la nube")

    def costo(self, orden: tuple[int, ...] | list[int]) -> float:
        """TODO: distancia del tour calculada al vuelo (sin matriz)."""
        raise NotImplementedError("TODO fase 2: costo con retorno, sin matriz densa")

    def validar(self, orden: tuple[int, ...] | list[int]) -> None:
        """TODO: tour canónico abierto igual que Viajero."""
        raise NotImplementedError("TODO fase 2: validar tour canónico")

    def _generar_candidatos(self) -> Iterator[tuple[int, ...]]:
        """TODO: permutaciones canónicas (lazy); exigir_enumerable corta n grande."""
        raise NotImplementedError("TODO fase 2: permutaciones lazy")
        yield  # pragma: no cover - hace generador
