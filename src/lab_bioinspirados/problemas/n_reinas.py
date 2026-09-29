"""N-reinas (stub TODO para estudiantes).

Objetivo: colocar n reinas sin ataques (filas, columnas, diagonales).
Función objetivo a escribir: ``costo(orden)`` = nº de pares en conflicto
(0 = resuelto, minimizar). Representación: ``orden[c] = fila`` de la reina
en la columna ``c`` (permutación de 0..n-1, canónica empieza en 0? no: aquí
el 0 inicial NO aplica; documenta tu convención).

Caso chico esperado a mano: n=4 → óptimo costo=0, p. ej. orden=(1, 3, 0, 2).
"""

from __future__ import annotations

from typing import ClassVar, Iterator

from lab_bioinspirados.nucleo.problema import Problema

PENDIENTE = True


class NReinas(Problema):
    """TODO estudiantes: implementa costo, validar, _generar_candidatos."""

    NOMBRE: ClassVar[str] = "n-reinas"
    PENDIENTE: ClassVar[bool] = True
    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 0

    def __init__(self, n: int = 4) -> None:
        self._n = int(n)

    @property
    def nombre(self) -> str:
        return f"N-reinas-n{self._n}"

    @property
    def tamano(self) -> int:
        return self._n

    def costo(self, orden: tuple[int, ...] | list[int]) -> float:
        """TODO: nº de pares de reinas que se atacan (0 = tablero válido)."""
        raise NotImplementedError("TODO estudiante: cuenta conflictos por diagonales")

    def validar(self, orden: tuple[int, ...] | list[int]) -> None:
        """TODO: permutación de 0..n-1 (una reina por columna y fila)."""
        raise NotImplementedError("TODO estudiante: valida permutación exacta")

    def _generar_candidatos(self) -> Iterator[tuple[int, ...]]:
        """TODO: yield de permutaciones (lazy con yield, no lista)."""
        raise NotImplementedError("TODO estudiante: genera permutaciones lazy")
        yield  # pragma: no cover - hace generador
