"""OneMax didáctico binario (stub TODO para estudiantes).

Objetivo: el problema más simple para depurar solvers binarios.
Función objetivo a escribir: ``costo(orden)`` = nº de ceros (= n - suma),
minimizar; el óptimo es todo unos con costo 0.

Caso chico esperado a mano: n=3 → óptimo orden=(1, 1, 1), costo=0.0.
Sirve para probar primero-gana y enumeración 2^n antes de la mochila.
"""

from __future__ import annotations

from typing import ClassVar, Iterator

from lab_bioinspirados.nucleo.problema import Problema

PENDIENTE = True


class OneMax(Problema):
    """TODO estudiantes: implementa costo, validar, _generar_candidatos."""

    NOMBRE: ClassVar[str] = "one-max"
    PENDIENTE: ClassVar[bool] = True
    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 0

    def __init__(self, n: int = 3) -> None:
        self._n = int(n)

    @property
    def nombre(self) -> str:
        return f"OneMax-n{self._n}"

    @property
    def tamano(self) -> int:
        return self._n

    def espacio(self) -> int:
        return 2**self._n

    def costo(self, orden: tuple[int, ...] | list[int]) -> float:
        """TODO: nº de ceros (n - suma de bits); óptimo 0 con todo unos."""
        raise NotImplementedError("TODO estudiante: costo = n - sum(orden)")

    def validar(self, orden: tuple[int, ...] | list[int]) -> None:
        """TODO: n bits 0/1 exactos."""
        raise NotImplementedError("TODO estudiante: valida bits 0/1")

    def _generar_candidatos(self) -> Iterator[tuple[int, ...]]:
        """TODO: yield del producto 2^n (lazy con itertools.product)."""
        raise NotImplementedError("TODO estudiante: genera 2^n vectores lazy")
        yield  # pragma: no cover - hace generador
