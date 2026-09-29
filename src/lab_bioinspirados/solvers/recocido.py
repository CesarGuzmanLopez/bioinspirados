"""Recocido simulado (plantilla TODO para estudiantes).

Contrato a usar:
- La mejor global solo se actualiza con ``<`` estricto (primero gana); la
  solución en curso acepta peores con Metropolis para escapar.
- Throttling: ``cada_n_pasos`` evaluaciones entre ``Paso``.
- Presupuestos: ``iteraciones`` y ``presupuesto_evaluaciones``.
- Parámetros: ``temperatura`` inicial (> 0), ``enfriamiento`` en (0, 1).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from lab_bioinspirados.nucleo.errores import ParametroInvalido, SolverPendiente
from lab_bioinspirados.nucleo.solver import Solver
from lab_bioinspirados.nucleo.tipos import Param, Solucion

if TYPE_CHECKING:
    from lab_bioinspirados.nucleo.problema import Problema


class RecocidoSimulado(Solver):
    """TODO estudiantes: enfriamiento + aceptación de Metropolis."""

    NOMBRE: ClassVar[str] = "recocido-simulado"
    PENDIENTE: ClassVar[bool] = True
    REQUIERE_ENUMERACION: ClassVar[bool] = False
    PARAMETROS: ClassVar[tuple[Param, ...]] = (
        Param("cada_n_pasos", 1000, "Emite un Paso al observador cada N evaluaciones."),
        Param(
            "presupuesto_evaluaciones",
            0,
            "0 = sin límite; >0 corta tras N evaluaciones (agotado=False).",
        ),
        Param("temperatura", 10.0, "Temperatura inicial (> 0)."),
        Param("enfriamiento", 0.95, "Factor geométrico en (0, 1)."),
        Param("iteraciones", 1000, "Pasos de la cadena."),
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
        if nombre == "temperatura" and (
            isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0
        ):
            raise ParametroInvalido("temperatura debe ser > 0", detalles={"valor": valor})
        if nombre == "enfriamiento" and (
            isinstance(valor, bool)
            or not isinstance(valor, (int, float))
            or not 0 < valor < 1
        ):
            raise ParametroInvalido("enfriamiento debe estar en (0, 1)", detalles={"valor": valor})

    def _resolver(self, problema: Problema) -> tuple[Solucion, int, bool, int]:
        raise SolverPendiente(
            "RecocidoSimulado pendiente. TODO: "
            "1) solución actual = inicial; T = temperatura; "
            "2) propone vecina; acepta si delta < 0 o azar < exp(-delta/T); "
            "3) mejor global solo con < estricto; T *= enfriamiento; "
            "4) throttling cada_n_pasos; devuelve (Solucion, evaluaciones, agotado, pasos)."
        )
