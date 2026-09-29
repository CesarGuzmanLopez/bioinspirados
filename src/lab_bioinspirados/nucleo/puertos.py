"""Puertos: lo que la Vista puede recibir + geometría opcional (solo stdlib)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterator, Protocol, runtime_checkable

from lab_bioinspirados.nucleo.tipos import LotePuntos, Paso, Resultado


@dataclass(frozen=True, slots=True)
class Informe:
    """Resumen inmutable listo para mostrar; la Vista nunca toca problemas/solvers."""

    titulo: str
    problema: str
    solver: str
    orden: tuple[int, ...]
    costo: float
    evaluaciones: int
    segundos: float
    agotado: bool
    pasos_emitidos: int
    veredicto: str = ""
    detalle: tuple[str, ...] = ()

    @classmethod
    def desde_resultado(
        cls,
        resultado: Resultado,
        titulo: str = "Informe",
        veredicto: str = "",
        detalle: tuple[str, ...] = (),
    ) -> Informe:
        """Puente Resultado → Informe (pull, sin importar capas)."""
        return cls(
            titulo=titulo,
            problema=resultado.problema,
            solver=resultado.solver,
            orden=tuple(resultado.solucion.orden),
            costo=resultado.solucion.costo,
            evaluaciones=resultado.evaluaciones,
            segundos=resultado.segundos,
            agotado=resultado.agotado,
            pasos_emitidos=resultado.pasos_emitidos,
            veredicto=veredicto,
            detalle=detalle,
        )


@runtime_checkable
class Vista(Protocol):
    """Puerto de salida: recibe Informe/Resultado, nunca problemas ni solvers."""

    def mostrar(self, resultado: Resultado) -> None:
        """Muestra un Resultado (puede construir el Informe dentro)."""
        ...

    def render(self, informe: Informe) -> None:
        """Dibuja un Informe ya construido."""
        ...


@runtime_checkable
class Geometria2D(Protocol):
    """Puerto pull opcional: el problema expone coordenadas si las tiene."""

    def coordenadas(self) -> tuple[tuple[float, float], ...] | None:
        """Coordenadas 2D o ``None`` si el problema no es geométrico."""
        ...


@dataclass(frozen=True, slots=True)
class Modelo:
    """Foto del problema para la vista viva: qué dibujar + cómo pedir lotes."""

    problema: str
    total: int
    dimensiones: int = 0
    lotes: Callable[..., Iterator[LotePuntos]] = field(default=lambda **_: iter(()), compare=False)

    @classmethod
    def desde_problema(cls, problema: object, lote: int = 4096, lod: int = 1) -> Modelo:
        """Puente problema → modelo (pull, sin importar capas concretas)."""
        nombre = getattr(problema, "nombre", type(problema).__name__)
        dimensiones = int(getattr(type(problema), "DIMENSIONES", 0))
        tamano = getattr(problema, "tamano", 0)
        try:
            total = int(tamano)
        except (TypeError, ValueError):
            total = 0

        def _lotes(**opciones: object) -> Iterator[LotePuntos]:
            tam_lote = int(opciones.get("lote", lote))  # type: ignore[arg-type]
            nivel = int(opciones.get("lod", lod))  # type: ignore[arg-type]
            yield from problema.stream_puntos(lote=tam_lote, lod=nivel)  # type: ignore[attr-defined]

        return cls(problema=str(nombre), total=total, dimensiones=dimensiones, lotes=_lotes)


@runtime_checkable
class VistaViva(Protocol):
    """Puerto vivo: recibe el modelo una vez y pasos de progreso después."""

    def on_modelo(self, modelo: Modelo) -> None:
        """Recibe la foto inicial del problema (geometría por lotes)."""
        ...

    def on_paso(self, paso: Paso) -> None:
        """Recibe cada foto de progreso del solver."""
        ...
