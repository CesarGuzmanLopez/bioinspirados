"""ABC Problema: qué es resolver bien + cómo enumerar candidatos (solo stdlib)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import factorial
from typing import ClassVar, Iterator

from lab_bioinspirados.nucleo.errores import (
    GeometriaNoDisponible,
    LoteInvalido,
    ProblemaDemasiadoGrande,
)
from lab_bioinspirados.nucleo.tipos import LotePuntos, Punto


class Problema(ABC):
    """Contrato que todo problema implementa.

    Tour canónico abierto: ``tuple[int, ...]`` que empieza en 0 y NO repite
    el 0 al final (el retorno ``orden[-1] -> orden[0]`` lo suma ``costo``).
    """

    LIMITE_ENUMERACION: ClassVar[int] = 10
    LIMITE_RECOMENDADO: ClassVar[int] = 10
    UMBRAL_ESPACIO_EXACTO: ClassVar[int] = 20
    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 0

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Etiqueta corta para informes (p. ej. ``"Viajero-n4"``)."""

    @property
    @abstractmethod
    def tamano(self) -> int:
        """Número de elementos del tour (``n``)."""

    @abstractmethod
    def costo(self, orden: tuple[int, ...] | list[int]) -> float:
        """Costo total incluyendo el retorno; puro y determinista."""

    @abstractmethod
    def validar(self, orden: tuple[int, ...] | list[int]) -> None:
        """No devuelve nada; lanza ``OrdenInvalido`` si el tour no es canónico."""

    @abstractmethod
    def _generar_candidatos(self) -> Iterator[tuple[int, ...]]:
        """Generador LAZY de tours canónicos (memoria O(1), con ``yield``)."""

    def exigir_resoluble(self) -> None:
        """Gancho: falla si la instancia quedó en estado no resoluble."""

    def exigir_enumerable(self) -> None:
        """Eager: falla solo si ``tamano`` supera lo recomendado SIN ``permitir_grande``.

        Ya no hay tope duro: con ``permitir_grande=True`` en el constructor
        la enumeración es un streaming lazy vivo (``yield`` uno por vez,
        memoria O(1)) que el solver recorre con presupuestos y cancelación.
        """
        limite = type(self).LIMITE_RECOMENDADO
        if self.tamano > limite and not getattr(self, "_permitir_grande", False):
            raise ProblemaDemasiadoGrande(
                f"tamano={self.tamano} supera LIMITE_RECOMENDADO={limite}: "
                "pasa permitir_grande=True para enumerar en streaming vivo "
                "(lazy, O(1) en memoria, córtalo con presupuestos)",
                detalles={
                    "tamano": self.tamano,
                    "limite": limite,
                    "pista": "permitir_grande=True",
                },
            )

    def _espacio_exacto(self) -> int:
        """Número exacto de candidatos (solo se llama con n chico, ver ``espacio``)."""
        return factorial(self.tamano - 1)

    def _estimar_espacio(self) -> str:
        """Estimación sin big-ints gigantes (no cuelga con n enorme)."""
        import math

        log10 = math.fsum(math.log10(i) for i in range(2, self.tamano))
        exp = int(log10)
        mantisa = 10 ** (log10 - exp)
        return f"≈{mantisa:.2f}e{exp} (estimación, n>{type(self).UMBRAL_ESPACIO_EXACTO})"

    def espacio(self) -> int | str:
        """Tours/candidatos: ``int`` exacto si n <= 20, si no ``str`` estimado.

        Nunca calcula un factorial gigante que cuelgue: pasado el umbral
        suma logaritmos y devuelve orden de magnitud.
        """
        if self.tamano <= type(self).UMBRAL_ESPACIO_EXACTO:
            return self._espacio_exacto()
        return self._estimar_espacio()

    def enumerar(self) -> Iterator[tuple[int, ...]]:
        """Template concreto: chequeo eager + delegación lazy.

        Es función normal (no generador) para que ``exigir_enumerable``
        falle al llamarla, no al primer ``next()``.
        """
        self.exigir_enumerable()
        return self._generar_candidatos()

    def _generar_puntos(self) -> Iterator[Punto] | None:
        """Gancho: puntos geométricos o ``None`` si no hay geometría.

        Default: puentea el puerto ``Geometria2D`` (método ``coordenadas``)
        si existe; si no hay método o devuelve ``None``, devuelve ``None``.
        """
        coordenadas = getattr(self, "coordenadas", None)
        if callable(coordenadas):
            puntos = coordenadas()
            if puntos is None:
                return None
            return (Punto(i=i, x=float(x), y=float(y)) for i, (x, y) in enumerate(puntos))
        return None

    def stream_puntos(self, lote: int = 4096, lod: int = 1) -> Iterator[LotePuntos]:
        """Template concreto: valida eager y entrega lotes inmutables.

        ``lod`` submuestrea (1 = todo, 2 = 1 de cada 2...). Falla eager con
        ``LoteInvalido`` si los parámetros son malos y con
        ``GeometriaNoDisponible`` si ``DIMENSIONES == 0`` o no hay puntos.
        Es función normal (no generador) para fallar al llamarla.
        """
        if isinstance(lote, bool) or not isinstance(lote, int) or lote < 1:
            raise LoteInvalido("lote debe ser int >= 1", detalles={"lote": lote})
        if isinstance(lod, bool) or not isinstance(lod, int) or lod < 1:
            raise LoteInvalido("lod debe ser int >= 1", detalles={"lod": lod})
        if type(self).DIMENSIONES == 0:
            raise GeometriaNoDisponible(
                f"{type(self).__name__} no tiene geometría (DIMENSIONES == 0)",
                detalles={"clase": type(self).__name__},
            )
        generador = self._generar_puntos()
        if generador is None:
            raise GeometriaNoDisponible(
                f"{type(self).__name__} no expone coordenadas",
                detalles={"clase": type(self).__name__},
            )
        filtrados = [p for i, p in enumerate(generador) if i % lod == 0]
        total = len(filtrados)

        def _lotes() -> Iterator[LotePuntos]:
            for inicio in range(0, total, lote):
                trozo = tuple(filtrados[inicio : inicio + lote])
                yield LotePuntos(puntos=trozo, inicio=inicio, total=total)

        return _lotes()
