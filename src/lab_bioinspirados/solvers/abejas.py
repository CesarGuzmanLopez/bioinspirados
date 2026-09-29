"""Abejas ABC - artificial bee colony (plantilla TODO para estudiantes).

Contrato a usar:
- Desempate ``<`` estricto al elegir la mejor fuente (primero gana).
- Throttling: ``cada_n_pasos`` evaluaciones entre ``Paso``.
- Presupuestos: ``iteraciones`` y ``presupuesto_evaluaciones``.
- Parámetros ABC: ``empleadas``, ``observadoras``, ``limite`` (abandonos
  antes de mandar exploradora).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from lab_bioinspirados.nucleo.errores import ParametroInvalido, SolverPendiente
from lab_bioinspirados.nucleo.solver import Solver
from lab_bioinspirados.nucleo.tipos import Param, Solucion

if TYPE_CHECKING:
    from lab_bioinspirados.nucleo.problema import Problema


class Abejas(Solver):
    """TODO estudiantes: ABC con empleadas / observadoras / exploradoras."""

    NOMBRE: ClassVar[str] = "abejas-abc"
    PENDIENTE: ClassVar[bool] = True
    REQUIERE_ENUMERACION: ClassVar[bool] = False
    PARAMETROS: ClassVar[tuple[Param, ...]] = (
        Param("cada_n_pasos", 1000, "Emite un Paso al observador cada N evaluaciones."),
        Param(
            "presupuesto_evaluaciones",
            0,
            "0 = sin límite; >0 corta tras N evaluaciones (agotado=False).",
        ),
        Param("empleadas", 10, "Fuentes activas (una por empleada)."),
        Param("observadoras", 10, "Observadoras que eligen por fitness."),
        Param("limite", 50, "Intentos sin mejora antes de abandonar la fuente."),
        Param("iteraciones", 100, "Ciclos empleada+observadora+exploradora."),
    )
    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 0

    def _validar_parametro(self, nombre: str, valor: object) -> None:
        if nombre in ("cada_n_pasos", "empleadas", "observadoras", "limite", "iteraciones"):
            if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:
                raise ParametroInvalido(
                    f"{nombre} debe ser int >= 1", detalles={"valor": valor}
                )
        if nombre == "presupuesto_evaluaciones" and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 0
        ):
            raise ParametroInvalido(
                "presupuesto_evaluaciones debe ser int >= 0", detalles={"valor": valor}
            )

    def _resolver(self, problema: Problema) -> tuple[Solucion, int, bool, int]:
        raise SolverPendiente(
            "Abejas pendiente. TODO: "
            "1) inicializa empleadas fuentes al azar; "
            "2) empleadas proponen vecina y aceptan si < (estricto); "
            "3) observadoras eligen por ruleta de fitness y explotan; "
            "4) si fuente supera limite → exploradora la reinicia; "
            "throttling cada_n_pasos; devuelve (Solucion, evaluaciones, agotado, pasos)."
        )
