"""Tipos inmutables del laboratorio (solo stdlib, sin lógica)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Solucion:
    """Mejor tour encontrado. ``orden`` es canónico abierto: empieza en 0."""

    orden: tuple[int, ...]
    costo: float


@dataclass(frozen=True, slots=True)
class Param:
    """Declaración de un parámetro configurable de un solver."""

    nombre: str
    defecto: object
    descripcion: str = ""


@dataclass(frozen=True, slots=True)
class Paso:
    """Foto de progreso emitida al observador cada ``cada_n_pasos`` evaluaciones."""

    numero: int
    evaluaciones: int
    mejor: Solucion


@dataclass(frozen=True, slots=True)
class Resultado:
    """Salida inmutable de ``Solver.resolver``. Lo construye el template, no el algoritmo."""

    problema: str
    solucion: Solucion
    solver: str
    evaluaciones: int
    segundos: float
    parametros: dict = field(default_factory=dict, compare=False)
    agotado: bool = True
    pasos_emitidos: int = 0
    motivo_corte: str = ""


@dataclass(frozen=True, slots=True)
class Punto:
    """Punto geométrico para streaming con LOD (fase 0, aditivo)."""

    i: int
    x: float
    y: float
    z: float | None = None


@dataclass(frozen=True, slots=True)
class LotePuntos:
    """Lote inmutable de puntos para la vista viva (streaming por lotes)."""

    puntos: tuple[Punto, ...]
    inicio: int = 0
    total: int = 0
