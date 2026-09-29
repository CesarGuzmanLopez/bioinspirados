"""Oráculo de verificación: primer-menor sobre ``enumerar()`` + doble pasada.

La doble pasada caza el bug clásico ``<=`` (quedarse con el ÚLTIMO en empates
en vez del primero): pasada 1 chequea costo óptimo, pasada 2 chequea que el
orden ganador sea el PRIMERO de la enumeración con ese costo.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from lab_bioinspirados.nucleo.tipos import Solucion

if TYPE_CHECKING:
    from lab_bioinspirados.nucleo.problema import Problema


def optimo_por_oraculo(problema: Problema) -> Solucion:
    """Oráculo bobo pero correcto: recorre ``enumerar()`` y se queda el primer menor (``<``)."""
    mejor_orden: tuple[int, ...] | None = None
    mejor_costo = float("inf")
    for orden in problema.enumerar():
        costo = problema.costo(orden)
        if costo < mejor_costo:
            mejor_orden = orden
            mejor_costo = costo
    assert mejor_orden is not None, "enumerar() vacío en problema resoluble"
    return Solucion(orden=mejor_orden, costo=mejor_costo)


def verificar(problema: Problema, solucion: Solucion) -> tuple[bool, bool]:
    """Doble pasada. Devuelve ``(ok_costo, ok_orden)``:

    - ``ok_costo``: el costo coincide con el óptimo del oráculo (idempotente).
    - ``ok_orden``: el orden es el PRIMERO con costo óptimo (caza ``<=``).
    """
    oraculo = optimo_por_oraculo(problema)
    ok_costo = problema.costo(list(solucion.orden)) == oraculo.costo == solucion.costo
    primero: tuple[int, ...] | None = None
    for orden in problema.enumerar():
        if problema.costo(orden) == oraculo.costo:
            primero = orden
            break
    ok_orden = primero is not None and tuple(solucion.orden) == tuple(primero)
    return (ok_costo, ok_orden)
