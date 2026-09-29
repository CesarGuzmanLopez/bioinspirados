"""Coloreo de grafos (stub TODO para estudiantes).

Objetivo: pintar vértices con k colores sin arista monocromática.
Función objetivo a escribir: ``costo(orden)`` = nº de aristas en conflicto
(0 = coloreo válido, minimizar). Representación: ``orden[v]`` = color
(0..k-1) del vértice ``v``.

Caso chico esperado a mano: triángulo (3 vértices, 3 aristas) con k=3
→ óptimo costo=0, p. ej. orden=(0, 1, 2); con k=2 → óptimo costo=1.
"""

from __future__ import annotations

from typing import ClassVar, Iterator

from lab_bioinspirados.nucleo.problema import Problema

PENDIENTE = True


class ColoreoGrafo(Problema):
    """TODO estudiantes: implementa costo, validar, _generar_candidatos."""

    NOMBRE: ClassVar[str] = "coloreo-grafos"
    PENDIENTE: ClassVar[bool] = True
    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 0

    def __init__(self, aristas: object = ((0, 1), (1, 2), (0, 2)), colores: int = 3) -> None:
        self._aristas = tuple(tuple(e) for e in list(aristas))  # type: ignore[arg-type]
        self._colores = int(colores)
        vertices = {v for e in self._aristas for v in e}
        self._n = (max(vertices) + 1) if vertices else 0

    @property
    def nombre(self) -> str:
        return f"Coloreo-n{self._n}-k{self._colores}"

    @property
    def tamano(self) -> int:
        return self._n

    def costo(self, orden: tuple[int, ...] | list[int]) -> float:
        """TODO: nº de aristas con ambos extremos del mismo color."""
        raise NotImplementedError("TODO estudiante: cuenta aristas monocromáticas")

    def validar(self, orden: tuple[int, ...] | list[int]) -> None:
        """TODO: n enteros en 0..k-1 (un color por vértice)."""
        raise NotImplementedError("TODO estudiante: valida colores en rango")

    def _generar_candidatos(self) -> Iterator[tuple[int, ...]]:
        """TODO: yield del producto k^n (lazy con itertools.product)."""
        raise NotImplementedError("TODO estudiante: genera k^n coloreos lazy")
        yield  # pragma: no cover - hace generador
