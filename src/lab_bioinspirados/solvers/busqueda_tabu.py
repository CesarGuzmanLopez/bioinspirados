"""Búsqueda tabú (plantilla TODO para estudiantes).

Contrato a usar:
- Desempate ``<`` estricto para la mejor global; para elegir vecina tabú se
  permite el mejor tabú solo si supera la aspiración.
- Throttling: ``cada_n_pasos`` evaluaciones entre ``Paso``.
- Presupuestos: ``iteraciones`` y ``presupuesto_evaluaciones``.
- Parámetros: ``tenencia`` (tamaño de la lista tabú), ``aspiracion``
  (si 1 = el tabú se perdona cuando mejora el óptimo).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from lab_bioinspirados.nucleo.errores import ParametroInvalido, SolverPendiente
from lab_bioinspirados.nucleo.solver import Solver
from lab_bioinspirados.nucleo.tipos import Param, Solucion

if TYPE_CHECKING:
    from lab_bioinspirados.nucleo.problema import Problema


class BusquedaTabu(Solver):
    """TODO estudiantes: lista tabú + criterio de aspiración."""

    NOMBRE: ClassVar[str] = "busqueda-tabu"
    PENDIENTE: ClassVar[bool] = True
    REQUIERE_ENUMERACION: ClassVar[bool] = False
    PARAMETROS: ClassVar[tuple[Param, ...]] = (
        Param("cada_n_pasos", 1000, "Emite un Paso al observador cada N evaluaciones."),
        Param(
            "presupuesto_evaluaciones",
            0,
            "0 = sin límite; >0 corta tras N evaluaciones (agotado=False).",
        ),
        Param("tenencia", 7, "Tamaño de la lista tabú (memoria corta)."),
        Param("aspiracion", 1, "1 = perdona tabú si mejora el óptimo; 0 = nunca."),
        Param("iteraciones", 500, "Iteraciones de búsqueda."),
    )
    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 0

    def _validar_parametro(self, nombre: str, valor: object) -> None:
        if nombre in ("cada_n_pasos", "tenencia", "iteraciones") and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 1
        ):
            raise ParametroInvalido(f"{nombre} debe ser int >= 1", detalles={"valor": valor})
        if nombre == "presupuesto_evaluaciones" and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 0
        ):
            raise ParametroInvalido(
                "presupuesto_evaluaciones debe ser int >= 0", detalles={"valor": valor}
            )
        if nombre == "aspiracion" and valor not in (0, 1):
            raise ParametroInvalido("aspiracion debe ser 0 o 1", detalles={"valor": valor})

    def _resolver(self, problema: Problema) -> tuple[Solucion, int, bool, int]:
        raise SolverPendiente(
            "BusquedaTabu pendiente. TODO: "
            "1) parte de solución inicial; lista tabú vacía (cola de tenencia); "
            "2) evalúa vecindad, elige mejor no-tabú (o tabú con aspiración si "
            "mejora el óptimo y aspiracion=1); "
            "3) actualiza mejor global solo con < estricto; "
            "4) throttling cada_n_pasos; devuelve (Solucion, evaluaciones, agotado, pasos)."
        )
