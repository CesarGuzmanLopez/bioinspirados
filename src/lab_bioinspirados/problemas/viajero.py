"""Viajero (TSP simétrico cuadrado). Único módulo que puede usar numpy (array)."""

from __future__ import annotations

from itertools import permutations
from math import dist
from typing import ClassVar, Iterator

from lab_bioinspirados.nucleo.errores import (
    MatrizInvalida,
    OrdenInvalido,
    ProblemaDemasiadoGrande,
)
from lab_bioinspirados.nucleo.problema import Problema

try:
    import numpy as np
except ImportError:  # pragma: no cover - numpy es dependencia, esto es plan B
    np = None


class Viajero(Problema):
    """TSP simétrico con matriz validada eager y guardada como tuple de tuples.

    Construcción: o ``matriz`` o ``coordenadas``, nunca ambas. Con coordenadas
    2D la matriz se deriva euclídea redondeada a 6 decimales calculando solo el
    triángulo superior y copiando el espejo (sin recalcular).
    """

    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 2
    LIMITE_MATRIZ: ClassVar[int] = 32
    LIMITE_RECOMENDADO: ClassVar[int] = 10
    LIMITE_ENUMERACION: ClassVar[int] = 10
    NOMBRE: ClassVar[str] = "viajero"
    ALIAS: ClassVar[tuple[str, ...]] = ("tsp-cuadrado", "TSPCuadrado")
    PENDIENTE: ClassVar[bool] = False

    def __init__(
        self,
        matriz: object = None,
        coordenadas: object = None,
        permitir_grande: bool = False,
    ) -> None:
        self._permitir_grande = bool(permitir_grande)
        if coordenadas is not None:
            if matriz is not None:
                raise MatrizInvalida("pasa matriz o coordenadas, no ambas")
            puntos = self._validar_coordenadas(coordenadas)
            if len(puntos) > self.LIMITE_RECOMENDADO and not self._permitir_grande:
                raise ProblemaDemasiadoGrande(
                    f"n={len(puntos)} supera LIMITE_RECOMENDADO={self.LIMITE_RECOMENDADO}: "
                    "pasa permitir_grande=True para enumerar en streaming vivo "
                    "(lazy, O(1) en memoria, córtalo con presupuestos)",
                    detalles={
                        "n": len(puntos),
                        "limite": self.LIMITE_RECOMENDADO,
                        "pista": "permitir_grande=True",
                    },
                )
            if len(puntos) > self.LIMITE_MATRIZ:
                # n grande + streaming: sin matriz densa; distancias al vuelo.
                if not self._permitir_grande:
                    raise ProblemaDemasiadoGrande(
                        f"n={len(puntos)} supera LIMITE_MATRIZ={self.LIMITE_MATRIZ}: "
                        "pasa permitir_grande=True para modo streaming "
                        "(coordenadas + distancia on-demand, sin matriz densa)",
                        detalles={
                            "n": len(puntos),
                            "limite": self.LIMITE_MATRIZ,
                            "pista": "permitir_grande=True",
                        },
                    )
                self._coordenadas: tuple[tuple[float, float], ...] | None = puntos
                self._matriz: tuple[tuple[float, ...], ...] | None = None
                self._tamano = len(puntos)
                return
            matriz = self._matriz_desde_coordenadas(puntos)
            self._coordenadas: tuple[tuple[float, float], ...] | None = puntos
        else:
            if matriz is None:
                raise MatrizInvalida("falta matriz o coordenadas para construir el TSP")
            n_previo = self._tamano_sin_alocar(matriz)
            if n_previo > self.LIMITE_RECOMENDADO and not self._permitir_grande:
                raise ProblemaDemasiadoGrande(
                    f"n={n_previo} supera LIMITE_RECOMENDADO={self.LIMITE_RECOMENDADO}: "
                    "pasa permitir_grande=True para enumerar en streaming vivo",
                    detalles={
                        "n": n_previo,
                        "limite": self.LIMITE_RECOMENDADO,
                        "pista": "permitir_grande=True",
                    },
                )
            if n_previo > self.LIMITE_MATRIZ and not self._permitir_grande:
                raise ProblemaDemasiadoGrande(
                    f"n={n_previo} supera LIMITE_MATRIZ={self.LIMITE_MATRIZ}: "
                    "usa TSPNube (streaming) en vez de matriz densa",
                    detalles={"n": n_previo, "limite": self.LIMITE_MATRIZ},
                )
            self._coordenadas = None
        self._matriz = self._validar_matriz(matriz)
        self._tamano = len(self._matriz)

    # -- construcción -----------------------------------------------------
    @staticmethod
    def _tamano_sin_alocar(matriz: object) -> int:
        """Cuenta n sin copiar la matriz (para fallar antes de alocar)."""
        try:
            import numpy as np  # type: ignore[import-not-found]

            if isinstance(matriz, np.ndarray):
                return int(matriz.shape[0]) if len(matriz.shape) == 2 else 0
        except ImportError:
            pass
        try:
            filas = list(matriz)  # type: ignore[arg-type]
            return len(filas)
        except TypeError:
            return 0

    @staticmethod
    def _validar_coordenadas(coordenadas: object) -> tuple[tuple[float, float], ...]:
        if hasattr(coordenadas, "tolist"):  # array numpy u objeto similar
            coordenadas = coordenadas.tolist()
        try:
            puntos = [(float(x), float(y)) for x, y in list(coordenadas)]
        except (TypeError, ValueError) as exc:
            raise MatrizInvalida("coordenadas deben ser pares (x, y) numéricos") from exc
        if len(puntos) < 2:
            raise MatrizInvalida("se necesitan al menos 2 coordenadas", detalles={"n": len(puntos)})
        import math

        for x, y in puntos:
            if not (math.isfinite(x) and math.isfinite(y)):
                raise MatrizInvalida("coordenadas deben ser finitas")
        return tuple(puntos)

    @staticmethod
    def _matriz_desde_coordenadas(
        puntos: tuple[tuple[float, float], ...],
    ) -> list[list[float]]:
        n = len(puntos)
        matriz = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                if np is not None:
                    d = float(np.hypot(puntos[i][0] - puntos[j][0], puntos[i][1] - puntos[j][1]))
                else:
                    d = dist(puntos[i], puntos[j])
                d = round(d, 6)
                matriz[i][j] = d
                matriz[j][i] = d  # espejo copiado, no recalculado
        return matriz

    @staticmethod
    def _validar_matriz(matriz: object) -> tuple[tuple[float, ...], ...]:
        if np is not None and isinstance(matriz, np.ndarray):
            matriz = matriz.tolist()
        try:
            filas = [list(fila) for fila in list(matriz)]
        except TypeError as exc:
            raise MatrizInvalida("la matriz debe ser una secuencia de filas") from exc
        n = len(filas)
        if n < 2:
            raise MatrizInvalida("n debe ser >= 2", detalles={"n": n})
        import math

        for fila in filas:
            if len(fila) != n:
                raise MatrizInvalida("la matriz debe ser cuadrada")
        valores: list[list[float]] = []
        for i, fila in enumerate(filas):
            fila_ok: list[float] = []
            for j, valor in enumerate(fila):
                if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                    raise MatrizInvalida("distancias numéricas", detalles={"i": i, "j": j})
                v = float(valor)
                if not math.isfinite(v) or v < 0:
                    raise MatrizInvalida("distancias finitas >= 0", detalles={"i": i, "j": j})
                fila_ok.append(v)
            valores.append(fila_ok)
        for i in range(n):
            if valores[i][i] != 0.0:
                raise MatrizInvalida(
                    "diagonal debe ser 0", detalles={"i": i, "valor": valores[i][i]}
                )
        for i in range(n):
            for j in range(i + 1, n):
                if valores[i][j] != valores[j][i]:
                    raise MatrizInvalida("la matriz debe ser simétrica", detalles={"i": i, "j": j})
        return tuple(tuple(fila) for fila in valores)

    # -- Problema ---------------------------------------------------------
    @property
    def nombre(self) -> str:
        return f"Viajero-n{self.tamano}"

    @property
    def tamano(self) -> int:
        return self._tamano

    def coordenadas(self) -> tuple[tuple[float, float], ...] | None:
        """Pull opcional (puerto Geometria2D): coordenadas o ``None``."""
        return self._coordenadas

    def _distancia(self, a: int, b: int) -> float:
        """Arista a→b: matriz si existe, si no euclídea on-demand (redondeo a 6)."""
        if self._matriz is not None:
            return self._matriz[a][b]
        assert self._coordenadas is not None  # modo streaming siempre tiene coords
        pa, pb = self._coordenadas[a], self._coordenadas[b]
        if np is not None:
            return round(float(np.hypot(pa[0] - pb[0], pa[1] - pb[1])), 6)
        return round(dist(pa, pb), 6)

    def validar(self, orden: tuple[int, ...] | list[int]) -> None:
        n = self.tamano
        if not isinstance(orden, (tuple, list)):
            raise OrdenInvalido("el orden debe ser tuple o list de ints")
        if len(orden) != n or any(isinstance(c, bool) or not isinstance(c, int) for c in orden):
            raise OrdenInvalido(f"tour de {n} ints canónicos", detalles={"orden": tuple(orden)})
        if orden[0] != 0:
            raise OrdenInvalido("el tour canónico empieza en 0", detalles={"orden": tuple(orden)})
        if sorted(orden) != list(range(n)):
            raise OrdenInvalido(
                f"permutación exacta de 0..{n - 1} sin repetir el 0 final",
                detalles={"orden": tuple(orden)},
            )

    def costo(self, orden: tuple[int, ...] | list[int]) -> float:
        self.validar(orden)
        total = 0.0
        for a, b in zip(orden, orden[1:]):
            total += self._distancia(a, b)
        return total + self._distancia(orden[-1], orden[0])  # retorno incluido

    def exigir_resoluble(self) -> None:
        if self.tamano < 2:  # imposible tras validación eager; cinturón y tirantes
            raise MatrizInvalida("n debe ser >= 2")

    def _generar_candidatos(self) -> Iterator[tuple[int, ...]]:
        for resto in permutations(range(1, self.tamano)):
            yield (0, *resto)


# Alias de compatibilidad: nombre histórico (ejemplos/tests/web previos a "Viajero").
TSPCuadrado = Viajero
