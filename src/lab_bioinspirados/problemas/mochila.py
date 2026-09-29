"""Mochila binaria 0/1 (problema completo para validar el núcleo sin TSP).

Óptimo conocido (docstring = oráculo a mano):
    pesos=(2, 3, 4, 5), valores=(3, 4, 5, 6), capacidad=5
    → óptimo orden=(1, 1, 0, 0), valor=7, costo=-7.0, peso=5.

Convención: minimizar, así que ``costo = -valor`` si cabe y ``inf`` si se
pasa (para que la fuerza bruta descarte sobrepesos sin lanzar). ``validar``
sí es estricta: binario exacto y capacidad (lanza ``OrdenInvalido``).
"""

from __future__ import annotations

from itertools import product
from typing import ClassVar, Iterator

from lab_bioinspirados.nucleo.errores import OrdenInvalido, ParametroInvalido
from lab_bioinspirados.nucleo.problema import Problema


class MochilaBinaria(Problema):
    """Mochila 0/1 con enumeración 2^n (tope ``LIMITE_ENUMERACION = 20``)."""

    LIMITE_ENUMERACION: ClassVar[int] = 20
    LIMITE_RECOMENDADO: ClassVar[int] = 20
    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 0
    NOMBRE: ClassVar[str] = "mochila-binaria"

    def __init__(
        self,
        pesos: object = (2, 3, 4, 5),
        valores: object = (3, 4, 5, 6),
        capacidad: int | float = 5,
        permitir_grande: bool = False,
    ) -> None:
        try:
            lista_pesos = [float(v) for v in list(pesos)]  # type: ignore[arg-type]
            lista_valores = [float(v) for v in list(valores)]  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise ParametroInvalido("pesos y valores deben ser secuencias numéricas") from exc
        if len(lista_pesos) != len(lista_valores) or not lista_pesos:
            raise ParametroInvalido(
                "pesos y valores con igual largo >= 1",
                detalles={"n_pesos": len(lista_pesos), "n_valores": len(lista_valores)},
            )
        import math

        for v in (*lista_pesos, *lista_valores, float(capacidad)):
            if not math.isfinite(v) or v < 0:
                raise ParametroInvalido("pesos/valores/capacidad finitos >= 0")
        self._pesos = tuple(lista_pesos)
        self._valores = tuple(lista_valores)
        self._capacidad = float(capacidad)
        self._permitir_grande = bool(permitir_grande)

    @property
    def nombre(self) -> str:
        return f"Mochila-binaria-n{self.tamano}-cap{self._capacidad:g}"

    @property
    def tamano(self) -> int:
        return len(self._pesos)

    def peso_de(self, orden: tuple[int, ...] | list[int]) -> float:
        """Peso total (sin validar capacidad, solo forma binaria mínima)."""
        return sum(p for p, bit in zip(self._pesos, orden) if bit)

    def valor_de(self, orden: tuple[int, ...] | list[int]) -> float:
        """Valor total."""
        return sum(v for v, bit in zip(self._valores, orden) if bit)

    def validar(self, orden: tuple[int, ...] | list[int]) -> None:
        n = self.tamano
        if not isinstance(orden, (tuple, list)) or len(orden) != n:
            raise OrdenInvalido(f"mochila de {n} bits 0/1", detalles={"orden": tuple(orden or ())})
        if any(isinstance(b, bool) or b not in (0, 1) for b in orden):
            raise OrdenInvalido("solo bits 0/1", detalles={"orden": tuple(orden)})
        if self.peso_de(orden) > self._capacidad:
            raise OrdenInvalido(
                f"peso excede capacidad={self._capacidad:g}",
                detalles={"peso": self.peso_de(orden), "capacidad": self._capacidad},
            )

    def costo(self, orden: tuple[int, ...] | list[int]) -> float:
        if not isinstance(orden, (tuple, list)) or len(orden) != self.tamano:
            raise OrdenInvalido("mochila: largo binario exacto")
        if any(isinstance(b, bool) or b not in (0, 1) for b in orden):
            raise OrdenInvalido("mochila: solo bits 0/1")
        if self.peso_de(orden) > self._capacidad:
            return float("inf")  # inf minimizando = descarta el sobrepeso
        return -self.valor_de(orden)  # minimizar = maximizar valor

    def _espacio_exacto(self) -> int:
        return 2**self.tamano

    def _estimar_espacio(self) -> str:
        return f"≈2^{self.tamano} (estimación, n>{type(self).UMBRAL_ESPACIO_EXACTO})"

    def _generar_candidatos(self) -> Iterator[tuple[int, ...]]:
        for bits in product((0, 1), repeat=self.tamano):
            yield tuple(bits)
