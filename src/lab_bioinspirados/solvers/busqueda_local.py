"""Búsqueda local (plantilla TODO para estudiantes).

Contrato a usar:
- Desempate ``<`` estricto: solo acepta vecino si mejora (el primero gana).
- Throttling: ``cada_n_pasos`` evaluaciones entre ``Paso``; añade
  ``cada_n_ms`` si quieres cortes por tiempo.
- Presupuestos: ``iteraciones`` y ``presupuesto_evaluaciones`` (0 = sin
  límite); al cortar, ``agotado=False`` + ``motivo_corte``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from lab_bioinspirados.nucleo.errores import ParametroInvalido, SolverPendiente
from lab_bioinspirados.nucleo.solver import Solver
from lab_bioinspirados.nucleo.tipos import Param, Solucion

if TYPE_CHECKING:
    from lab_bioinspirados.nucleo.problema import Problema


class BusquedaLocal(Solver):
    """TODO estudiantes: mejora iterativa por vecindad (p. ej. 2-opt en TSP)."""

    NOMBRE: ClassVar[str] = "busqueda-local"
    PENDIENTE: ClassVar[bool] = True
    REQUIERE_ENUMERACION: ClassVar[bool] = False
    PARAMETROS: ClassVar[tuple[Param, ...]] = (
        Param("cada_n_pasos", 1000, "Emite un Paso al observador cada N evaluaciones."),
        Param(
            "presupuesto_evaluaciones",
            0,
            "0 = sin límite; >0 corta tras N evaluaciones (agotado=False).",
        ),
        Param("iteraciones", 1000, "Iteraciones máximas de mejora."),
        Param("semilla", 0, "Semilla del arranque aleatorio (0 = determinista)."),
    )
    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 0

    def _validar_parametro(self, nombre: str, valor: object) -> None:
        if nombre in ("cada_n_pasos", "iteraciones") and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 1
        ):
            raise ParametroInvalido(f"{nombre} debe ser int >= 1", detalles={"valor": valor})
        if nombre == "presupuesto_evaluaciones" and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 0
        ):
            raise ParametroInvalido(
                "presupuesto_evaluaciones debe ser int >= 0", detalles={"valor": valor}
            )
        if nombre == "semilla" and (isinstance(valor, bool) or not isinstance(valor, int)):
            raise ParametroInvalido("semilla debe ser int", detalles={"valor": valor})

    def _resolver(self, problema: Problema) -> tuple[Solucion, int, bool, int]:
        raise SolverPendiente(
            "BusquedaLocal pendiente. TODO: "
            "1) solución inicial (azar con semilla o greedy); "
            "2) genera vecinos (2-opt / flip un bit según problema); "
            "3) acepta solo si costo < mejor (estricto); "
            "4) throttling cada_n_pasos + corta por iteraciones/presupuesto; "
            "5) devuelve (Solucion, evaluaciones, agotado, pasos)."
        )
