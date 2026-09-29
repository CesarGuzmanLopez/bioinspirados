"""Shim de compatibilidad: ``tsp`` re-exporta :class:`Viajero`.

Módulo histórico (albergaba ``TSPCuadrado``); el módulo real es
``lab_bioinspirados.problemas.viajero``. Se conserva para no romper imports
antiguos del estilo ``from lab_bioinspirados.problemas.tsp import TSPCuadrado``.
"""

from __future__ import annotations

from lab_bioinspirados.problemas.viajero import TSPCuadrado, Viajero

__all__ = ["TSPCuadrado", "Viajero"]
