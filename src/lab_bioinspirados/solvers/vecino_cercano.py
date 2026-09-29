"""Vecino cercano (plantilla TODO para estudiantes).

Contrato a usar:
- Desempate ``<`` estricto: el primero gana (igual que FuerzaBruta y oráculo).
- Throttling: emite ``Paso`` al observador cada ``cada_n_pasos``
  evaluaciones (y ``cada_n_ms`` si lo añades con ``perf_counter``).
- Presupuestos: ``presupuesto_evaluaciones`` (0 = sin límite); si cortas
  antes, ``agotado=False`` y ``motivo_corte`` explica por qué.
- Sin I/O ni ``print`` dentro del solver; todo progreso vía ``observador``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from lab_bioinspirados.nucleo.errores import ParametroInvalido, SolverPendiente
from lab_bioinspirados.nucleo.solver import Solver
from lab_bioinspirados.nucleo.tipos import Param, Solucion

if TYPE_CHECKING:
    from lab_bioinspirados.nucleo.problema import Problema


class VecinoCercano(Solver):
    """TODO estudiantes: greedy que desde el 0 visita siempre la más cercana."""

    NOMBRE: ClassVar[str] = "vecino-cercano"
    PENDIENTE: ClassVar[bool] = True
    REQUIERE_ENUMERACION: ClassVar[bool] = False
    PARAMETROS: ClassVar[tuple[Param, ...]] = (
        Param("cada_n_pasos", 1000, "Emite un Paso al observador cada N evaluaciones."),
        Param(
            "presupuesto_evaluaciones",
            0,
            "0 = sin límite; >0 corta tras N evaluaciones (agotado=False).",
        ),
    )
    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 0

    def _validar_parametro(self, nombre: str, valor: object) -> None:
        if nombre == "cada_n_pasos" and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 1
        ):
            raise ParametroInvalido("cada_n_pasos debe ser int >= 1", detalles={"valor": valor})
        if nombre == "presupuesto_evaluaciones" and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 0
        ):
            raise ParametroInvalido(
                "presupuesto_evaluaciones debe ser int >= 0", detalles={"valor": valor}
            )

    def _resolver(self, problema: Problema) -> tuple[Solucion, int, bool, int]:
        raise SolverPendiente(
            "VecinoCercano pendiente. TODO: "
            "1) orden=[0], visitados={0}; "
            "2) mientras falten: evalúa distancias con problema.costo(parcial)? "
            "no: usa matriz/geometría vía costo de aristas; "
            "3) elige el menor con < estricto (primero gana); "
            "4) notifica cada cada_n_pasos; "
            "5) devuelve (Solucion, evaluaciones, agotado, pasos)."
        )
